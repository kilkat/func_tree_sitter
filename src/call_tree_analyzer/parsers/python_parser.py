from typing import Optional
from tree_sitter import Node
from tree_sitter_languages import get_parser

from .base import BaseParser

class PythonParser(BaseParser):
    """Python 언어 파서"""
    
    def __init__(self):
        super().__init__("python")
        self.tree_sitter_parser = get_parser("python")
    
    def is_function_node(self, node: Node) -> bool:
        return node.type == "function_definition"
    
    def is_call_node(self, node: Node) -> bool:
        return node.type == "call"
    
    def extract_function_name(self, node: Node, source_code: bytes) -> Optional[str]:
        if not self.is_function_node(node):
            return None
        
        name_node = node.child_by_field_name("name")
        if name_node and name_node.type == "identifier":
            return self.get_node_text(source_code, name_node)
        
        return None
    
    def extract_call_target(self, node: Node, source_code: bytes) -> Optional[str]:
        if not self.is_call_node(node):
            return None
        
        func_node = node.child_by_field_name("function")
        if not func_node:
            return None
        
        # 단순 함수 호출: func()
        if func_node.type == "identifier":
            return self.get_node_text(source_code, func_node)
        
        # 속성 접근: obj.method()
        if func_node.type == "attribute":
            attr_node = func_node.child_by_field_name("attribute")
            if attr_node:
                return self.get_node_text(source_code, attr_node)
        
        return None
    
    def should_include_function(self, func_name: str) -> bool:
        if not func_name:
            return False
        
        # 매직 메서드와 private 메서드 제외 옵션
        if func_name.startswith('__') and func_name.endswith('__'):
            return func_name in {'__init__', '__main__'}  # 특정 매직 메서드만 포함
        
        return True
    
    def should_include_call(self, call_name: str) -> bool:
        if not call_name:
            return False
        
        # 내장 함수들 제외
        builtin_functions = {
            'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 
            'set', 'tuple', 'range', 'enumerate', 'zip', 'map', 'filter'
        }
        
        return call_name not in builtin_functions