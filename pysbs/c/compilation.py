from pysbs.c.deps import CDependencyStep
from pysbs.c.project import CProject
from pysbs.misc.exec_step import ExecBuildStep, ExecArgument
from pathlib import Path
import os.path
from zlib import adler32


class CCompilationStep(ExecBuildStep):
    """
    Step to compile given `.c` file into given `.o` file.
    """

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
    def input_files(self) -> list[Path]:
        return [self.input]

    @property
    def input_version(self) -> str:
        return str(os.path.getmtime(self.input))


class CAutoCompilationStep(CCompilationStep):
    """
    Convenience step to compile `.c` file into some file in given build folder.
    File name and placement is left for this step to chose.

    Also automatically creates dependency step for that input file.
    """

    def __init__(self, project: CProject, input: Path, build_dir : Path, dependencies=[], command='g++', flags=[]) -> None:
        self.obj_dir = build_dir / 'objects'
        self.output = self.obj_dir / (input.stem + '_' + str(adler32(str(input).encode())) + '.o')
        super().__init__(project, input, self.output, dependencies + [
            CDependencyStep(project, input)
        ], command, flags)

    async def run(self):
        self.obj_dir.mkdir(parents=True, exist_ok=True)
        return await super().run()
