# Add project folder to path
import sys
from os.path import dirname, join, getmtime
sys.path.append(dirname(dirname(dirname(__file__))))

from pysbs.core.step import BuildStep
from pysbs.core.build import build
from pysbs.core.config import use_database

class FoobarBuildStep(BuildStep):

    def __init__(self, file, dependencies=[]) -> None:
        super().__init__(dependencies)
        self.file = file
        self.name = file

    @property
    def step_id(self):
        return self.file

    @property
    def input_version(self) -> str:
        return str(getmtime(self.file))

    def run(self):
        self.print(f'Compiling `{self.file}`')
        with open(self.file, 'r') as f:
            conts = f.read()
            if 'fail' in conts:
                self.print('Something wrong in the file')
                self.fail()

use_database(join(dirname(__file__), 'pysbs.db'))

lib = FoobarBuildStep('./src/lib.foobar')
other = FoobarBuildStep('./src/other.foobar', dependencies=[lib])
main = FoobarBuildStep('./src/main.foobar', dependencies=[lib, other])

build(main)
