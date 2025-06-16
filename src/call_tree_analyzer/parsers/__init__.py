from .base import BaseParser
from .c_parser import CParser
from .python_parser import PythonParser
from .javascript_parser import JavaScriptParser

# 언어별 파서 매핑
PARSER_CLASSES = {
    "c": CParser,
    "python": PythonParser,
    "javascript": JavaScriptParser,
}

def get_parser(language: str) -> BaseParser:
    """언어에 맞는 파서 인스턴스 반환"""
    parser_class = PARSER_CLASSES.get(language)
    if not parser_class:
        raise ValueError(f"지원하지 않는 언어: {language}")
    
    return parser_class()

def get_supported_languages() -> list[str]:
    """지원하는 언어 목록 반환"""
    return list(PARSER_CLASSES.keys())

__all__ = [
    'BaseParser',
    'CParser', 
    'PythonParser',
    'JavaScriptParser',
    'get_parser',
    'get_supported_languages'
]