from typing import Dict, List
from pathlib import Path

# 언어별 설정
LANGUAGE_CONFIG = {
    "c": {
        "extensions": [".c", ".h"],
        "parser_name": "c",
        "function_node_types": ["function_definition"],
        "call_node_types": ["call_expression"],
        "comment_patterns": ["//", "/*", "*/"]
    },
    "python": {
        "extensions": [".py"],
        "parser_name": "python", 
        "function_node_types": ["function_definition"],
        "call_node_types": ["call"],
        "comment_patterns": ["#", '"""', "'''"]
    },
    "javascript": {
        "extensions": [".js", ".jsx", ".ts", ".tsx"],
        "parser_name": "javascript",
        "function_node_types": ["function_declaration", "function_expression", "arrow_function"],
        "call_node_types": ["call_expression"],
        "comment_patterns": ["//", "/*", "*/"]
    }
}

# 분석 설정
ANALYSIS_CONFIG = {
    "max_file_size_mb": 10,  # 최대 파일 크기 (MB)
    "max_recursion_depth": 1000,  # 최대 재귀 깊이
    "ignore_patterns": [
        "*.pyc", "*.pyo", "__pycache__", ".git", ".svn", 
        "node_modules", "build", "dist", ".pytest_cache"
    ],
    "include_anonymous_functions": False,  # 익명 함수 포함 여부
    "include_builtin_calls": False  # 내장 함수 호출 포함 여부
}

def get_language_by_extension(extension: str) -> str:
    """확장자로 언어 찾기"""
    for lang, config in LANGUAGE_CONFIG.items():
        if extension.lower() in config["extensions"]:
            return lang
    return None

def get_supported_extensions() -> List[str]:
    """지원하는 모든 확장자 반환"""
    extensions = []
    for config in LANGUAGE_CONFIG.values():
        extensions.extend(config["extensions"])
    return list(set(extensions))

def should_ignore_path(path: Path) -> bool:
    """경로가 무시 패턴에 해당하는지 확인"""
    path_str = str(path)
    for pattern in ANALYSIS_CONFIG["ignore_patterns"]:
        if pattern in path_str:
            return True
    return False