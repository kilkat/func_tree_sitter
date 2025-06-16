from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

@dataclass
class FunctionCall:
    """함수 호출 정보"""
    name: str
    line: int
    column: Optional[int] = None
    
    def __str__(self) -> str:
        return f"{self.name} (line {self.line})"

@dataclass
class FunctionInfo:
    """함수 정의 정보"""
    name: str
    file_path: Path
    line: int
    column: Optional[int] = None
    calls: List[FunctionCall] = None
    
    def __post_init__(self):
        if self.calls is None:
            self.calls = []
    
    @property
    def full_name(self) -> str:
        """파일 경로를 포함한 전체 함수 이름"""
        return f"{self.file_path}::{self.name}"
    
    def add_call(self, call: FunctionCall):
        """함수 호출 추가"""
        self.calls.append(call)
    
    def get_call_count(self) -> int:
        """호출 횟수 반환"""
        return len(self.calls)