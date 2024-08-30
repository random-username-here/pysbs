from pathlib import Path
from typing import Optional

class CProject:
    """
    Class, object of which contains some common information
    for all steps of compiling C/C++ project, like flags
    and include paths.
    """

    def __init__(self, include_paths = []) -> None:
        self.include_paths = [
            *list(include_paths)
        ]

    def resolve_include(self, file : Path, included : str) -> Optional[Path]:
        """
        Resolve include, written in given file.
        """
        for i in [file.parent] + self.include_paths:
            path = i / included
            if path.exists():
                return path
        return None
