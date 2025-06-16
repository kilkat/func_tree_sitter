import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter

from .config import get_supported_extensions, should_ignore_path, ANALYSIS_CONFIG

logger = logging.getLogger(__name__)

class FileScanner:
    """파일 시스템 스캐너"""
    
    def __init__(self):
        self.supported_extensions = set(get_supported_extensions())
    
    def scan_directory(self, root_path: Path) -> List[Path]:
        """디렉터리를 재귀적으로 스캔하여 소스 파일 찾기"""
        source_files = []
        
        try:
            for file_path in root_path.rglob("*"):
                if self._is_valid_source_file(file_path):
                    source_files.append(file_path)
        
        except PermissionError as e:
            logger.warning(f"권한 없음: {e}")
        except Exception as e:
            logger.error(f"디렉터리 스캔 중 오류: {e}")
        
        return sorted(source_files)
    
    def _is_valid_source_file(self, file_path: Path) -> bool:
        """유효한 소스 파일인지 확인"""
        try:
            # 파일인지 확인
            if not file_path.is_file():
                return False
            
            # 무시 패턴 확인
            if should_ignore_path(file_path):
                return False
            
            # 확장자 확인
            if file_path.suffix.lower() not in self.supported_extensions:
                return False
            
            # 파일 크기 확인
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > ANALYSIS_CONFIG["max_file_size_mb"]:
                return False
            
            return True
            
        except (OSError, PermissionError):
            return False

class ProgressTracker:
    """진행상황 추적기"""
    
    def __init__(self, show_progress: bool = True):
        self.show_progress = show_progress
        self.total = 0
        self.current = 0
        self.start_time = 0
    
    def start(self, total: int):
        """진행상황 추적 시작"""
        self.total = total
        self.current = 0
        self.start_time = time.time()
        
        if self.show_progress:
            print(f"분석 시작: {total}개 파일")
    
    def update(self, increment: int = 1):
        """진행상황 업데이트"""
        self.current += increment
        
        if self.show_progress and self.total > 0:
            percentage = (self.current / self.total) * 100
            elapsed = time.time() - self.start_time
            
            if self.current > 0:
                eta = (elapsed / self.current) * (self.total - self.current)
                print(f"\r진행: {self.current}/{self.total} ({percentage:.1f}%) "
                      f"경과: {elapsed:.1f}s ETA: {eta:.1f}s", end="")
    
    def finish(self):
        """진행상황 추적 완료"""
        if self.show_progress:
            elapsed = time.time() - self.start_time
            print(f"\n완료: {elapsed:.1f}초")

@dataclass
class ErrorInfo:
    """오류 정보"""
    category: str
    message: str
    context: str = ""
    timestamp: float = field(default_factory=time.time)

class ErrorHandler:
    """오류 처리 및 수집기"""
    
    def __init__(self):
        self.errors: List[ErrorInfo] = []
        self.error_counts: Counter = Counter()
    
    def log_error(self, category: str, message: str, context: str = ""):
        """오류 로깅"""
        error_info = ErrorInfo(
            category=category,
            message=message,
            context=context
        )
        
        self.errors.append(error_info)
        self.error_counts[category] += 1
        
        logger.error(f"[{category}] {message} {context}")
    
    def has_errors(self) -> bool:
        """오류가 있는지 확인"""
        return len(self.errors) > 0
    
    def get_summary(self) -> Dict[str, int]:
        """오류 요약 반환"""
        return dict(self.error_counts)
    
    def get_errors_by_category(self, category: str) -> List[ErrorInfo]:
        """카테고리별 오류 목록"""
        return [error for error in self.errors if error.category == category]

class StatisticsCalculator:
    """통계 계산기"""
    
    @staticmethod
    def calculate_complexity_metrics(call_tree) -> Dict[str, float]:
        """복잡도 메트릭 계산"""
        functions = call_tree.functions
        
        if not functions:
            return {}
        
        # 기본 통계
        total_functions = len(functions)
        total_calls = sum(len(func.calls) for func in functions.values())
        
        # 호출 복잡도 (함수당 평균 호출 수)
        avg_calls_per_function = total_calls / total_functions if total_functions > 0 else 0
        
        # 팬인/팬아웃 분석
        caller_counts = defaultdict(int)  # 각 함수를 호출하는 함수의 수
        callee_counts = {}  # 각 함수가 호출하는 함수의 수
        
        for func_name, func_info in functions.items():
            callee_counts[func_name] = len(func_info.calls)
            
            for call in func_info.calls:
                caller_counts[call.name] += 1
        
        # 최대/평균 팬인/팬아웃
        max_fan_in = max(caller_counts.values()) if caller_counts else 0
        max_fan_out = max(callee_counts.values()) if callee_counts else 0
        avg_fan_in = sum(caller_counts.values()) / len(caller_counts) if caller_counts else 0
        avg_fan_out = sum(callee_counts.values()) / len(callee_counts) if callee_counts else 0
        
        return {
            "total_functions": total_functions,
            "total_calls": total_calls,
            "avg_calls_per_function": avg_calls_per_function,
            "max_fan_in": max_fan_in,
            "max_fan_out": max_fan_out,
            "avg_fan_in": avg_fan_in,
            "avg_fan_out": avg_fan_out
        }
    
    @staticmethod
    def find_hotspots(call_tree) -> Dict[str, List[str]]:
        """핫스팟 분석 (많이 호출되는 함수, 많이 호출하는 함수 등)"""
        functions = call_tree.functions
        
        # 호출 빈도 계산
        call_frequency = defaultdict(int)
        for func_info in functions.values():
            for call in func_info.calls:
                call_frequency[call.name] += 1
        
        # 상위 호출되는 함수들
        most_called = sorted(call_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 가장 많이 호출하는 함수들
        most_calling = sorted(
            [(name, len(info.calls)) for name, info in functions.items()],
            key=lambda x: x[1], reverse=True
        )[:10]
        
        # 고아 함수들 (호출되지 않는 함수)
        orphaned = call_tree.get_orphaned_functions()
        
        return {
            "most_called_functions": [name for name, count in most_called],
            "most_calling_functions": [name for name, count in most_calling],
            "orphaned_functions": [func.full_name for func in orphaned[:10]]
        }

class CodeFormatter:
    """코드 출력 포매터"""
    
    @staticmethod
    def format_call_tree_text(call_tree) -> str:
        """호출 트리를 텍스트로 포맷"""
        lines = []
        lines.append("=== Call Tree Analysis ===\n")
        
        for func_name, func_info in sorted(call_tree.functions.items()):
            lines.append(f"{func_name} ({func_info.file_path}:{func_info.line})")
            
            if func_info.calls:
                for call in func_info.calls:
                    lines.append(f"  └─ {call.name} (line {call.line})")
            else:
                lines.append("  └─ (no calls)")
            
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_statistics(stats: Dict[str, float]) -> str:
        """통계를 텍스트로 포맷"""
        lines = []
        lines.append("=== Statistics ===")
        
        for key, value in stats.items():
            if isinstance(value, float):
                lines.append(f"{key}: {value:.2f}")
            else:
                lines.append(f"{key}: {value}")
        
        return "\n".join(lines)

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """로깅 설정"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

def validate_project_path(path: str) -> Path:
    """프로젝트 경로 유효성 검사"""
    project_path = Path(path).resolve()
    
    if not project_path.exists():
        raise FileNotFoundError(f"경로가 존재하지 않습니다: {project_path}")
    
    if not project_path.is_dir():
        raise ValueError(f"디렉터리가 아닙니다: {project_path}")
    
    return project_path