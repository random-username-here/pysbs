import os.path
from pathlib import Path
import re

import logging
from pysbs.c.project import CProject
from pysbs.core.step import BuildStep
from pysbs.misc.include_finder import find_includes, ExcludedZoneSpec

INCLUDE_RE = re.compile(r'#include ((?:<[^>]+>)|(?:"[^"]+"))')

C_EXCLUDED_ZONES = [
    # Comments
    ExcludedZoneSpec('/*', '*/', is_ignored_by_parser=True),
    ExcludedZoneSpec('//', '\n', is_ignored_by_parser=True),
    # Strings
    ExcludedZoneSpec('"', '"', has_escapes = True)
]

class CDependencyStep(BuildStep):
    """
    Step which makes C file depend on files it includes
    Usefull for making C sources depend on C headers.
    """

    def __init__(self, project : CProject, path : Path):
        super().__init__()
        self.project = project
        self.path = path

    def __postinit__(self):
        super().__postinit__()

        if self.project.is_not_part_of_project(self.path):
            return

        if self.input_version != self.ns.get('include_cache_version', ''):
            logging.debug(f'Searching includes in {self.path}')
            self.compute_deps()
        
        logging.debug(f'Resolving includes in {self.path}')

        for i in self.ns['includes']:
            resolved = self.project.resolve_include(self.path, i)
            if resolved:
                if not self.project.is_not_part_of_project(resolved):
                    self.dependencies.append(CDependencyStep(self.project, resolved))
            else:
                logging.warn(f'Could not resolve include `{i}` in file `{self.path}`')

    def compute_deps(self):
        with open(self.path, 'r') as f:
            source = f.read()
        include_matches = find_includes(
            source, C_EXCLUDED_ZONES, INCLUDE_RE
        )
        # Regex matches `<foo.h>` or `"foo.h"`
        includes = [i.group(1)[1:-1] for i in include_matches]
        self.ns['includes'] = includes
        self.ns['include_cache_version'] = self.input_version

    @property
    def step_id(self) -> str:
        return 'CDependencyStep { ' + str(self.path) + ' }'

    @property
    def input_version(self) -> str:
       return str(os.path.getmtime(self.path))
