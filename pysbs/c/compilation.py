from pysbs.c.project import CProject
from pysbs.misc.exec_step import ExecBuildStep, ExecArgument
from pathlib import Path
import os.path


class CCompilationStep(ExecBuildStep):

    FLAGS = [
        ExecArgument('-fdiagnostics-color', 'cflag')
    ]

    def __init__(self, project : CProject, input : Path, output : Path, dependencies=[], command='g++', flags=[]) -> None:
        super().__init__(command, dependencies, [
            ExecArgument(input, 'path'),
            '-o', ExecArgument(output, 'path'),
            *[ ExecArgument('-I' + str(i), 'include') for i in project.include_paths ],
            '-c',
            *self.FLAGS,
            *flags
        ])
        self.name = 'Compile ' + str(input)
        self.input = input

    @property
    def input_version(self) -> str:
        return str(os.path.getmtime(self.input))
