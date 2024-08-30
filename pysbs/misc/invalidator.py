"""
In this file we check if the build script changed.
"""

from collections.abc import Callable
from dataclasses import dataclass
import os
import re
import sys
from pathlib import Path
import importlib.machinery
from typing import Optional

import logging

from pysbs.core.config import get_database
from .include_finder import find_includes, ExcludedZoneSpec


PYTHON_EXCLUDED_ZONES = [
    # Comments
    ExcludedZoneSpec(begin='#', end='\n'),
    
    # Docstrings
    ExcludedZoneSpec(begin='"""', end='"""', has_escapes=True),
    ExcludedZoneSpec(begin="'''", end="'''", has_escapes=True),

    # Normal strings
    ExcludedZoneSpec(begin='"', end='"', has_escapes=True),
    ExcludedZoneSpec(begin='\'', end='\'', has_escapes=True)
]

PYTHON_IMPORT_MATCHER = re.compile(r'(?:from ([^\s\n]+) import )|(?:import ([^\s\n]+))')

IGNORED_PATHS = [
    Path(re.__file__).parent.parent, # Builtin location
]

ESC_FILE = "\x1b[94;4m" #] blue underlined
ESC_RESET = "\x1b[0m" #]
ESC_MSG_THEME = "\x1b[94m" #]
MSG_PREF = ESC_MSG_THEME + ' █  ' + ESC_RESET

def is_builtin(file):
    for i in IGNORED_PATHS:
        if i in file.parents:
            return True
    return False



def find_python_imports(file : Path, path : list[str] = sys.path) -> list[tuple[Path,str]]:
    """
    Finds list of files included from given `source`
    """

    if file.suffixes[-1] != '.py':
        return []

    for i in IGNORED_PATHS:
        if i in file.parents:
            return []

    logging.debug(f'Searching for imports in {file}')

    matches = find_includes(file.read_text(), PYTHON_EXCLUDED_ZONES, PYTHON_IMPORT_MATCHER)

    names = [ list(filter(bool, i.groups()))[0] for i in matches ]

    def find_module_path(modname : str, path : list[str]) -> Optional[str]:

        name, submod, *_ = modname.split('.', 1) + [None,]
        spec = importlib.machinery.PathFinder.find_spec(name, path)
        
        if spec is None:
            return None

        if submod is None:
            return spec.origin
        else:
            if spec.submodule_search_locations is None:
                return None
            return find_module_path(submod, spec.submodule_search_locations)

    def resolve(name : str):
        if name[0] == '.':
            loc = find_module_path(name[1:], [str(file.parent)])
            mname = name.rsplit('.', 1)[0] + name 
            return loc, mname
        else:
            return find_module_path(name, path), name

    files = [ resolve(i) for i in names ]
    files = [ (Path(i[0]), i[1]) for i in files if i[0] and not is_builtin(Path(i[0])) ]

    return files

@dataclass
class DeptreeFile:
    path : Path
    modname : str
    deps : list['DeptreeFile']

def make_python_deptree(top : Path, bounds : Path = Path('/')) -> DeptreeFile:
    """Make dependency tree of given file, including files only from `bouds` folder"""

    files = {}

    def add_file(path : Path, modname : str) -> DeptreeFile:
        if path in files:
            return files[path]

        node = DeptreeFile(
            path=path,
            modname=modname,
            deps=list()
        )
        
        files[path] = node

        for file, modname in find_python_imports(path):
            if bounds not in file.parents:
                continue
            node.deps.append(add_file(file, modname))

        return node

    return add_file(top, '__main__')


def walk_deptree(tree : DeptreeFile, callable : Callable[[DeptreeFile], None]):

    visited = set()

    def fn(item : DeptreeFile):
        if item.path in visited:
            return
        visited.add(item.path)

        for i in item.deps:
            fn(i)
        
        callable(item)

    fn(tree)


def invalidate_if_needed(script : Path, project_bounds : Path):

    ns = get_database().get_ns('invalidator')

    print('Resolving build script dependency tree...')
    tree = make_python_deptree(script, project_bounds)

    changed = False

    def check_changed(file : DeptreeFile):
        nonlocal changed
        old = ns.get(str(file.path), -1)
        cur = os.path.getmtime(file.path)

        if old != cur:
            changed = True
            print()
            print(MSG_PREF + ESC_MSG_THEME + 'Detected change in build script' + ESC_RESET)
            print(MSG_PREF)
            print(MSG_PREF + f'  file   : {ESC_FILE}{file.path}{ESC_RESET}')
            print(MSG_PREF + f'  module : {ESC_FILE}{file.modname}{ESC_RESET}')
            print(MSG_PREF)
            print(MSG_PREF + 'Will rebuild everything...')
            raise StopIteration

    try:
        walk_deptree(tree, check_changed)
    except StopIteration:
        pass

    if not changed:
        return

    get_database().get_ns('steps').drop()

    def update_versions(file : DeptreeFile):
        ns[str(file.path)] = os.path.getmtime(file.path)

    walk_deptree(tree, update_versions)

