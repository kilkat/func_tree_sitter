import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Optional

from .analyzer import CallTreeAnalyzer, FileAnalyzer
from .utils import setup_logging, validate_project_path, CodeFormatter, StatisticsCalculator
from .models import CallTree

def create_parser() -> argparse.ArgumentParser:
    """CLI 인자 파서 생성"""
    parser = argparse.ArgumentParser(
        description="코드 호출 트리 분석기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  %(prog)s /path/to/project                    # 프로젝트 분석
  %(prog)s /path/to/project -o output.json     # JSON 파일로 저장
  %(prog)s /path/to/project --format text      # 텍스트 형태로 출력
  %(prog)s /path/to/file.py --single-file      # 단일 파일 분석
        """
    )
    
    parser.add_argument(
        "path",
        help="분석할 프로젝트 디렉터리 또는 파일 경로"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="출력 파일 경로"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["json", "text"],
        default="json",
        help="출력 형식 (기본값: json)"
    )
    
    parser.add_argument(
        "--single-file",
        action="store_true",
        help="단일 파일 분석 모드"
    )
    
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=4,
        help="병렬 처리 워커 수 (기본값: 4)"
    )
    
    parser.add_argument(
        "--stats",
        action="store_true",
        help="통계 정보 표시"
    )
    
    parser.add_argument(
        "--hotspots",
        action="store_true",
        help="핫스팟 분석 결과 표시"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="로그 레벨 (기본값: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        help="로그 파일 경로"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="최소한의 출력만 표시"
    )
    
    return parser

def analyze_project(args) -> CallTree:
    """프로젝트 분석 실행"""
    if args.single_file:
        analyzer = FileAnalyzer()
        return analyzer.analyze_single_file(args.path)
    else:
        project_path = validate_project_path(args.path)
        analyzer = CallTreeAnalyzer(max_workers=args.workers)
        return analyzer.analyze_project(str(project_path))

def format_output(call_tree: CallTree, format_type: str, include_stats: bool = False, 
                 include_hotspots: bool = False) -> str:
    """출력 포맷팅"""
    if format_type == "json":
        # CallTree를 JSON 직렬화 가능한 형태로 변환
        data = {
            "functions": {}
        }
        
        for func_name, func_info in call_tree.functions.items():
            data["functions"][func_name] = {
                "name": func_info.name,
                "file": str(func_info.file_path),
                "line": func_info.line,
                "column": func_info.column,
                "calls": [
                    {
                        "name": call.name,
                        "line": call.line,
                        "column": call.column
                    }
                    for call in func_info.calls
                ]
            }
        
        # 통계 추가
        if include_stats:
            data["statistics"] = StatisticsCalculator.calculate_complexity_metrics(call_tree)
        
        # 핫스팟 추가
        if include_hotspots:
            data["hotspots"] = StatisticsCalculator.find_hotspots(call_tree)
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    elif format_type == "text":
        result = CodeFormatter.format_call_tree_text(call_tree)
        
        if include_stats:
            stats = StatisticsCalculator.calculate_complexity_metrics(call_tree)
            result += "\n" + CodeFormatter.format_statistics(stats)
        
        if include_hotspots:
            hotspots = StatisticsCalculator.find_hotspots(call_tree)
            result += "\n=== Hotspots ===\n"
            
            result += "\nMost Called Functions:\n"
            for func in hotspots["most_called_functions"][:5]:
                result += f"  - {func}\n"
            
            result += "\nMost Calling Functions:\n"
            for func in hotspots["most_calling_functions"][:5]:
                result += f"  - {func}\n"
            
            result += "\nOrphaned Functions:\n"
            for func in hotspots["orphaned_functions"][:5]:
                result += f"  - {func}\n"
        
        return result
    
    else:
        raise ValueError(f"지원하지 않는 출력 형식: {format_type}")

def write_output(content: str, output_path: Optional[str]):
    """결과 출력"""
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"결과가 저장되었습니다: {output_path}")
    else:
        print(content)

def main():
    """CLI 메인 함수"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 로깅 설정
    if not args.quiet:
        setup_logging(args.log_level, args.log_file)
    else:
        setup_logging("ERROR", args.log_file)
    
    try:
        # 분석 실행
        call_tree = analyze_project(args)
        
        # 결과 포맷팅
        output = format_output(
            call_tree, 
            args.format,
            include_stats=args.stats,
            include_hotspots=args.hotspots
        )
        
        # 출력
        write_output(output, args.output)
        
    except KeyboardInterrupt:
        print("\n분석이 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"오류 발생: {e}")
        if args.log_level == "DEBUG":
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()