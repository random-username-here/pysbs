import json
from pysbs.c.project import CProject
from pysbs.misc.exec_step import ExecBuildStep, ExecArgument
from pathlib import Path
import os.path


class CLinkingStep(ExecBuildStep):

    FLAGS = [
        ExecArgument('-fdiagnostics-color', 'cflag')
    ]

    def __init__(self, project : CProject, inputs : list[Path], output : Path, dependencies=[], command='g++', flags=[]) -> None:
        super().__init__(command, dependencies, [
            *[ ExecArgument(i, 'path') for i in inputs],
            '-o', ExecArgument(output, 'path'),
            *self.FLAGS,
            *flags
        ])
        self.name = 'Link ' + str(output)
        self.inputs = inputs

    @property
    def input_files(self) -> list[Path]:
        return self.inputs

