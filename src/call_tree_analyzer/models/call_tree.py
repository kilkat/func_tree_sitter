from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from pathlib import Path
from .function import FunctionInfo, FunctionCall

@dataclass
class CallTree:
    """호출 트리 전체 구조"""
    functions: Dict[str, FunctionInfo] = field(default_factory=dict)
    
    def add_function(self, func_info: FunctionInfo):
        """함수 정보 추가"""
        self.functions[func_info.full_name] = func_info
    
    def get_function(self, full_name: str) -> Optional[FunctionInfo]:
        """함수 정보 조회"""
        return self.functions.get(full_name)
    
    def get_callers(self, function_name: str) -> List[FunctionInfo]:
        """특정 함수를 호출하는 함수들 반환"""
        callers = []
        for func_info in self.functions.values():
            for call in func_info.calls:
                if call.name == function_name:
                    callers.append(func_info)
                    break
        return callers
    
    def get_callees(self, function_name: str) -> List[FunctionCall]:
        """특정 함수가 호출하는 함수들 반환"""
        func_info = self.get_function(function_name)
        return func_info.calls if func_info else []
    
    def get_all_functions(self) -> List[str]:
        """모든 함수 이름 반환"""
        return list(self.functions.keys())
    
    def get_orphaned_functions(self) -> List[FunctionInfo]:
        """호출되지 않는 함수들 (진입점 후보) 반환"""
        called_functions = set()
        for func_info in self.functions.values():
            for call in func_info.calls:
                called_functions.add(call.name)
        
        orphaned = []
        for func_info in self.functions.values():
            if func_info.name not in called_functions:
                orphaned.append(func_info)
        
        return orphaned

class CallTreeBuilder:
    """호출 트리 빌더 클래스"""
    
    def __init__(self):
        self.call_tree = CallTree()
    
    def add_function_definition(self, name: str, file_path: Path, 
                             line: int, column: Optional[int] = None) -> FunctionInfo:
        """함수 정의 추가"""
        func_info = FunctionInfo(
            name=name,
            file_path=file_path,
            line=line,
            column=column
        )
        self.call_tree.add_function(func_info)
        return func_info
    
    def add_function_call(self, caller_full_name: str, callee_name: str, 
                         line: int, column: Optional[int] = None):
        """함수 호출 추가"""
        caller = self.call_tree.get_function(caller_full_name)
        if caller:
            call = FunctionCall(name=callee_name, line=line, column=column)
            caller.add_call(call)
    
    def build(self) -> CallTree:
        """완성된 호출 트리 반환"""
        return self.call_tree