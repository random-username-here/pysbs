import asyncio
from pathlib import Path
import sys

THIS_FILE = Path(__file__)
THIS_FOLDER = THIS_FILE.parent
sys.path.append(str(THIS_FILE.parent.parent.parent))

from pysbs.c import CProject, CLinkingStep, CCompilationStep, CDependencyStep
from pysbs.core import use_database, build
from zlib import adler32

BUILD_FOLDER = THIS_FOLDER / 'build'
INCLUDE_FOLDER = THIS_FOLDER / 'include'
SRC_FOLDER = THIS_FOLDER / 'src'
OUT_FILE = BUILD_FOLDER / 'hello.out'

use_database(BUILD_FOLDER / 'pysbs.db')

project = CProject()
project.include_paths.append(INCLUDE_FOLDER)

sources = SRC_FOLDER.glob('**/*.c')

def make_compilation_step(file : Path):
    output = BUILD_FOLDER / (file.stem + '_' + str(adler32(str(file).encode())) + '.o')
    return output, CCompilationStep(
            project, file, output,
            [CDependencyStep(project, file)]
        )

compilation_steps = [
    make_compilation_step(i) for i in sources
]

linking_step = CLinkingStep(
    project,
    inputs=[ i[0] for i in compilation_steps ],
    output=OUT_FILE,
    dependencies=[ i[1] for i in compilation_steps ]
)

asyncio.run(build(linking_step))


