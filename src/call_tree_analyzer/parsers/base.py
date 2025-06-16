from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pathlib import Path
from tree_sitter import Node, Tree

from ..models import FunctionInfo, FunctionCall
from ..config import LANGUAGE_CONFIG

class BaseParser(ABC):
    """언어별 파서의 기본 클래스"""
    
    def __init__(self, language: str):
        self.language = language
        self.config = LANGUAGE_CONFIG.get(language, {})
        self.tree_sitter_parser = None
    
    @abstractmethod
    def extract_function_name(self, node: Node, source_code: bytes) -> Optional[str]:
        """함수 이름 추출"""
        pass
    
    @abstractmethod
    def extract_call_target(self, node: Node, source_code: bytes) -> Optional[str]:
        """함수 호출 대상 추출"""
        pass
    
    @abstractmethod
    def is_function_node(self, node: Node) -> bool:
        """함수 정의 노드인지 확인"""
        pass
    
    @abstractmethod
    def is_call_node(self, node: Node) -> bool:
        """함수 호출 노드인지 확인"""
        pass
    
    def get_node_text(self, source_code: bytes, node: Node) -> str:
        """노드의 텍스트 추출"""
        return source_code[node.start_byte:node.end_byte].decode("utf-8")
    
    def get_node_position(self, node: Node) -> tuple[int, int]:
        """노드의 위치 (line, column) 반환"""
        return node.start_point[0] + 1, node.start_point[1]
    
    def parse_file(self, file_path: Path) -> Optional[Tree]:
        """파일 파싱"""
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
            return self.tree_sitter_parser.parse(source_code)
        except Exception as e:
            print(f"파일 파싱 실패: {file_path} - {e}")
            return None
    
    def should_include_function(self, func_name: str) -> bool:
        """함수를 분석 결과에 포함할지 결정"""
        # 언어별로 오버라이드 가능
        return func_name and not func_name.startswith('_')
    
    def should_include_call(self, call_name: str) -> bool:
        """함수 호출을 분석 결과에 포함할지 결정"""
        # 언어별로 오버라이드 가능
        return call_name and not call_name.startswith('_')