from typing import Optional
from tree_sitter import Node
from tree_sitter_languages import get_parser

from .base import BaseParser

class JavaScriptParser(BaseParser):
    """JavaScript 언어 파서"""
    
    def __init__(self):
        super().__init__("javascript")
        self.tree_sitter_parser = get_parser("javascript")
    
    def is_function_node(self, node: Node) -> bool:
        return node.type in ["function_declaration", "function_expression", "arrow_function"]
    
    def is_call_node(self, node: Node) -> bool:
        return node.type == "call_expression"
    
    def extract_function_name(self, node: Node, source_code: bytes) -> Optional[str]:
        if node.type == "function_declaration":
            name_node = node.child_by_field_name("name")
            if name_node and name_node.type == "identifier":
                return self.get_node_text(source_code, name_node)
        
        elif node.type == "function_expression":
            name_node = node.child_by_field_name("name")
            if name_node and name_node.type == "identifier":
                return self.get_node_text(source_code, name_node)
            else:
                return "<anonymous>"
        
        elif node.type == "arrow_function":
            return "<arrow_function>"
        
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
        
        # 멤버 함수 호출: obj.method()
        if func_node.type == "member_expression":
            property_node = func_node.child_by_field_name("property")
            if property_node:
                return self.get_node_text(source_code, property_node)
        
        return None
    
    def should_include_function(self, func_name: str) -> bool:
        if not func_name:
            return False
        
        # 익명 함수 포함 여부는 설정에 따라
        if func_name in ["<anonymous>", "<arrow_function>"]:
            return self.config.get("include_anonymous_functions", False)
        
        return True