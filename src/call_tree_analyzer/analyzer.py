from pathlib import Path
from typing import Optional, List, Dict, Set
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import CallTree, CallTreeBuilder, ProjectInfo, FileInfo, FunctionInfo, FunctionCall
from .parsers import get_parser, get_supported_languages
from .config import get_language_by_extension, should_ignore_path, ANALYSIS_CONFIG
from .utils import FileScanner, ProgressTracker, ErrorHandler

logger = logging.getLogger(__name__)

class CallTreeAnalyzer:
    """호출 트리 분석기 메인 클래스"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.builder = CallTreeBuilder()
        self.project_info = None
        self.error_handler = ErrorHandler()
        self.progress_tracker = ProgressTracker()
        
        # 파서 캐시
        self._parser_cache: Dict[str, object] = {}
    
    def analyze_project(self, project_root: str) -> CallTree:
        """프로젝트 전체 분석"""
        root_path = Path(project_root).resolve()
        
        if not root_path.exists():
            raise FileNotFoundError(f"프로젝트 경로가 존재하지 않습니다: {root_path}")
        
        if not root_path.is_dir():
            raise ValueError(f"프로젝트 경로가 디렉터리가 아닙니다: {root_path}")
        
        logger.info(f"프로젝트 분석 시작: {root_path}")
        
        # 프로젝트 정보 초기화
        self.project_info = ProjectInfo(root_path=root_path)
        
        try:
            # 1. 파일 스캔
            scanner = FileScanner()
            source_files = scanner.scan_directory(root_path)
            
            if not source_files:
                logger.warning("분석할 소스 파일을 찾을 수 없습니다.")
                return self.builder.build()
            
            logger.info(f"발견된 소스 파일: {len(source_files)}개")
            
            # 2. 프로젝트 정보 구성
            self._build_project_info(source_files)
            
            # 3. 병렬 파일 분석
            self._analyze_files_parallel(source_files)
            
            # 4. 후처리
            call_tree = self.builder.build()
            self._post_process(call_tree)
            
            logger.info(f"분석 완료: 함수 {len(call_tree.functions)}개")
            
            return call_tree
            
        except Exception as e:
            logger.error(f"프로젝트 분석 중 오류 발생: {e}")
            self.error_handler.log_error("project_analysis", str(e))
            raise
    
    def analyze_file(self, file_path: Path) -> Optional[FileInfo]:
        """단일 파일 분석"""
        if should_ignore_path(file_path):
            return None
        
        language = get_language_by_extension(file_path.suffix)
        if not language:
            return None
        
        try:
            # 파일 크기 확인
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > ANALYSIS_CONFIG["max_file_size_mb"]:
                logger.warning(f"파일 크기가 너무 큽니다: {file_path} ({file_size_mb:.1f}MB)")
                return None
            
            # 파서 가져오기
            parser = self._get_parser(language)
            if not parser:
                return None
            
            # 파일 파싱
            tree = parser.parse_file(file_path)
            if not tree:
                return None
            
            # AST 순회 및 분석
            source_code = file_path.read_bytes()
            function_count = self._analyze_ast(
                tree.root_node, 
                source_code, 
                parser, 
                file_path, 
                None
            )
            
            # 파일 정보 생성
            line_count = len(source_code.decode('utf-8', errors='ignore').splitlines())
            file_info = FileInfo(
                path=file_path,
                language=language,
                line_count=line_count,
                function_count=function_count
            )
            
            return file_info
            
        except Exception as e:
            logger.error(f"파일 분석 실패: {file_path} - {e}")
            self.error_handler.log_error("file_analysis", str(e), str(file_path))
            return None
    
    def _build_project_info(self, source_files: List[Path]):
        """프로젝트 정보 구성"""
        for file_path in source_files:
            language = get_language_by_extension(file_path.suffix)
            if language:
                file_info = FileInfo(path=file_path, language=language)
                self.project_info.add_file(file_info)
    
    def _analyze_files_parallel(self, source_files: List[Path]):
        """병렬로 파일들 분석"""
        self.progress_tracker.start(len(source_files))
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 작업 제출
            future_to_file = {
                executor.submit(self.analyze_file, file_path): file_path 
                for file_path in source_files
            }
            
            # 결과 처리
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    file_info = future.result()
                    if file_info:
                        self.project_info.files[file_path] = file_info
                    
                    self.progress_tracker.update()
                    
                except Exception as e:
                    logger.error(f"파일 분석 중 예외 발생: {file_path} - {e}")
        
        self.progress_tracker.finish()
    
    def _analyze_ast(self, node, source_code: bytes, parser, file_path: Path, 
                    current_func: Optional[str], depth: int = 0) -> int:
        """AST 노드 재귀 분석"""
        
        # 재귀 깊이 제한
        if depth > ANALYSIS_CONFIG["max_recursion_depth"]:
            logger.warning(f"재귀 깊이 제한 도달: {file_path}")
            return 0
        
        function_count = 0
        
        # 함수 정의 처리
        if parser.is_function_node(node):
            func_name = parser.extract_function_name(node, source_code)
            
            if func_name and parser.should_include_function(func_name):
                line, column = parser.get_node_position(node)
                
                # 함수 정보 생성 및 추가
                func_info = self.builder.add_function_definition(
                    name=func_name,
                    file_path=file_path,
                    line=line,
                    column=column
                )
                
                current_func = func_info.full_name
                function_count += 1
        
        # 함수 호출 처리
        elif parser.is_call_node(node):
            call_name = parser.extract_call_target(node, source_code)
            
            if (call_name and current_func and 
                parser.should_include_call(call_name)):
                
                line, column = parser.get_node_position(node)
                
                # 함수 호출 추가
                self.builder.add_function_call(
                    caller_full_name=current_func,
                    callee_name=call_name,
                    line=line,
                    column=column
                )
        
        # 자식 노드 재귀 처리
        for child in node.children:
            function_count += self._analyze_ast(
                child, source_code, parser, file_path, current_func, depth + 1
            )
        
        return function_count
    
    def _get_parser(self, language: str):
        """파서 캐시에서 가져오기"""
        if language not in self._parser_cache:
            try:
                self._parser_cache[language] = get_parser(language)
            except Exception as e:
                logger.error(f"파서 생성 실패: {language} - {e}")
                return None
        
        return self._parser_cache[language]
    
    def _post_process(self, call_tree: CallTree):
        """분석 후처리"""
        # 통계 로깅
        total_functions = len(call_tree.functions)
        total_calls = sum(len(func.calls) for func in call_tree.functions.values())
        orphaned_functions = len(call_tree.get_orphaned_functions())
        
        logger.info(f"분석 결과 통계:")
        logger.info(f"  - 전체 함수: {total_functions}개")
        logger.info(f"  - 전체 호출: {total_calls}개")
        logger.info(f"  - 고아 함수: {orphaned_functions}개")
        
        # 에러 요약
        if self.error_handler.has_errors():
            error_summary = self.error_handler.get_summary()
            logger.warning(f"분석 중 오류 발생: {error_summary}")

class FileAnalyzer:
    """단일 파일 전용 분석기"""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
    
    def analyze_single_file(self, file_path: str) -> CallTree:
        """단일 파일만 분석"""
        analyzer = CallTreeAnalyzer(max_workers=1)
        
        # 임시 프로젝트로 처리
        file_path = Path(file_path)
        parent_dir = file_path.parent
        
        return analyzer.analyze_project(str(parent_dir))
    
    def get_file_functions(self, file_path: str) -> List[FunctionInfo]:
        """파일의 함수 목록만 추출"""
        call_tree = self.analyze_single_file(file_path)
        
        file_path = Path(file_path)
        functions = []
        
        for func_info in call_tree.functions.values():
            if func_info.file_path == file_path:
                functions.append(func_info)
        
        return functions