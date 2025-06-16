from dataclasses import dataclass, field
from typing import Dict, List, Set
from pathlib import Path

@dataclass
class FileInfo:
    """파일 정보"""
    path: Path
    language: str
    line_count: int = 0
    function_count: int = 0
    
    @property
    def extension(self) -> str:
        return self.path.suffix

@dataclass  
class ProjectInfo:
    """프로젝트 전체 정보"""
    root_path: Path
    files: Dict[Path, FileInfo] = field(default_factory=dict)
    supported_languages: Set[str] = field(default_factory=set)
    
    def add_file(self, file_info: FileInfo):
        """파일 정보 추가"""
        self.files[file_info.path] = file_info
        self.supported_languages.add(file_info.language)
    
    def get_files_by_language(self, language: str) -> List[FileInfo]:
        """언어별 파일 목록 반환"""
        return [info for info in self.files.values() 
                if info.language == language]
    
    def get_total_line_count(self) -> int:
        """전체 라인 수 반환"""
        return sum(info.line_count for info in self.files.values())
    
    def get_total_function_count(self) -> int:
        """전체 함수 수 반환"""
        return sum(info.function_count for info in self.files.values())