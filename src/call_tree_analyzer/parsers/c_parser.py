from typing import Optional
from tree_sitter import Node
from tree_sitter_languages import get_parser

from .base import BaseParser

class CParser(BaseParser):
    """C 언어 파서"""
    
    def __init__(self):
        super().__init__("c")
        self.tree_sitter_parser = get_parser("c")
    
    def is_function_node(self, node: Node) -> bool:
        return node.type == "function_definition"
    
    def is_call_node(self, node: Node) -> bool:
        return node.type == "call_expression"
    
    def extract_function_name(self, node: Node, source_code: bytes) -> Optional[str]:
        if not self.is_function_node(node):
            return None
        
        # function_definition -> function_declarator -> identifier
        declarator = node.child_by_field_name("declarator")
        if not declarator:
            return None
        
        # 포인터나 배열 선언을 처리하기 위해 재귀적으로 탐색
        current = declarator
        while current and current.type != "identifier":
            if current.type == "function_declarator":
                current = current.child_by_field_name("declarator")
            elif current.type == "pointer_declarator":
                current = current.child_by_field_name("declarator")
            else:
                break
        
        if current and current.type == "identifier":
            return self.get_node_text(source_code, current)
        
        return None
    
    def extract_call_target(self, node: Node, source_code: bytes) -> Optional[str]:
        if not self.is_call_node(node):
            return None
        
        func_node = node.child_by_field_name("function")
        if func_node and func_node.type == "identifier":
            return self.get_node_text(source_code, func_node)
        
        # 함수 포인터 호출이나 멤버 함수 호출 처리
        if func_node and func_node.type == "field_expression":
            field = func_node.child_by_field_name("field")
            if field:
                return self.get_node_text(source_code, field)
        
        return None
    
    def should_include_function(self, func_name: str) -> bool:
        # C의 경우 main 함수와 static 함수도 포함
        if not func_name:
            return False
        
        # 시스템 함수들은 제외
        system_functions = {'printf', 'scanf', 'malloc', 'free', 'strlen', 'strcpy'}
        return func_name not in system_functions