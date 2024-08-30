from pathlib import Path
import sys

THIS_FILE = Path(__file__)
THIS_FOLDER = THIS_FILE.parent
sys.path.append(str(THIS_FILE.parent.parent.parent))
##### Begin build code

from pysbs.c import CProject, CLinkingStep, CAutoCompilationStep
from pysbs.core import use_database, build
from pysbs.misc.exec_step import generate_compile_commands
import asyncio

# Misc. files and folders

BUILD_FOLDER = THIS_FOLDER / 'build'
INCLUDE_FOLDER = THIS_FOLDER / 'include'
SRC_FOLDER = THIS_FOLDER / 'src'
OUT_FILE = BUILD_FOLDER / 'hello.out'
SOURCES = SRC_FOLDER.glob('**/*.c')

# Setup folder structure

BUILD_FOLDER.mkdir(parents=True, exist_ok=True)
use_database(BUILD_FOLDER / 'pysbs.db')

# Create a project

project = CProject(
    include_paths=[INCLUDE_FOLDER]
)

# Make compilation steps for each source

compilation_steps = [
    CAutoCompilationStep(project, i, BUILD_FOLDER)
    for i in SOURCES
]

# Add step to link them together

linking_step = CLinkingStep(
    project,
    inputs=[ i.output for i in compilation_steps ],
    output=OUT_FILE,
    dependencies=compilation_steps
)

# Build!

generate_compile_commands([linking_step], BUILD_FOLDER / 'compile_commands.json', THIS_FOLDER)
asyncio.run(build(linking_step))


