import asyncio
import sys
from os.path import dirname, join, getmtime

sys.path.append(dirname(dirname(dirname(__file__))))

import json
import os.path
from pathlib import Path
from pysbs.core import use_database
from pysbs.misc.exec_step import ExecBuildStep, ExecArgument
from pysbs.core.build import build

class CompileStep(ExecBuildStep):
    def __init__(self, output : Path, inputs : list[Path], dependencies = []) -> None:
        super().__init__('gcc',
                dependencies,
                ['-o', ExecArgument(output, 'path')] + 
                [ ExecArgument(i, 'path') for i in inputs ] + 
                [ ExecArgument('-fdiagnostics-color', 'cflag') ])
        self.inputs = inputs
        self.name = 'Compiling into ' + str(output)

    @property
    def input_version(self) -> str:
        rs = json.dumps([ os.path.getmtime(i) for i in  self.inputs ])
        return rs

async def main():

    THIS_FOLDER = Path(__file__).parent

    use_database(THIS_FOLDER / 'pysbs.db')

    source = THIS_FOLDER / 'test.c'
    output = THIS_FOLDER / 'helloworld'

    compilation = CompileStep(output, [source])

    await build(compilation)

asyncio.run(main())
