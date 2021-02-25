from typing import List, Optional

class FileSystemEvent:
    src_path: str

class FileSystemEventHandler:
    pass

class PatternMatchingEventHandler(FileSystemEventHandler):
    def __init__(
        self,
        patterns: List[str],
        ignore_patterns: Optional[List[str]],
        ignore_directories: bool,
        case_sensitive: bool,
    ): ...
