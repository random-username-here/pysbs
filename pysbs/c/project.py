from pathlib import Path
from typing import Optional

SYSTEM_INCLUDE_FOLDERS = [
    # FIXME: find those paths
    Path('/usr/include'),
    Path('/usr/lib/gcc/x86_64-pc-linux-gnu/14.2.1/include/')
]

class CProject:
    """
    Class, object of which contains some common information
    for all steps of compiling C/C++ project, like flags
    and include paths.
    """

    def __init__(self) -> None:
        self.include_paths = [
            *SYSTEM_INCLUDE_FOLDERS
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

    def is_not_part_of_project(self, file : Path):
        """Check if given header is not a part of a project, but part of stdlib/something other"""
        for i in SYSTEM_INCLUDE_FOLDERS:
            if i in file.parents:
                return True
        return False
