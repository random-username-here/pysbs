import subprocess
import asyncio.subprocess
import json
import os

from pathlib import Path
from typing import Any, Literal
from dataclasses import dataclass
from collections.abc import Callable

from pysbs.core.step import BuildStep
from pysbs.misc.walk import walk_deps

### Escape codes for coloring output

ESC_GRAY = '\x1b[90m' #]
ESC_RESET = '\x1b[0m' #]
ESC_BOLD = '\x1b[1m' #]
ESC_RED = '\x1b[91m' #]
ESC_BLUE = '\x1b[94m' #]
ESC_CYAN = '\x1b[96m' #]
ESC_GREEN = '\x1b[92m' #] for paths
ESC_UNDERLINE = '\x1b[4m' #] for paths

### Line width to wrap arguments by

BEST_LINE_WIDTH = 120

### Misc. strings used when printing command

CMD_PREF = f'{ESC_GRAY} $ {ESC_RESET}'
CMD_ARGS_PREF = f'{ESC_GRAY} :   {ESC_RESET}'

### Formatters used to color command arguments

FormatterName = Literal[
    'normal', # Normal, not highlighted argument
    'path',   # Path argument, highlighted as link
    'cflag',  # C flag, like -Wall. First letter is colored diffrently.
    'include' # C include path, like -I/usr/share/lib/foobar. 
]

FORMATTERS : dict[FormatterName, Callable[[str], str]] = {
        'normal': lambda s : s,
        'path': lambda path : ESC_BLUE + ESC_UNDERLINE + path + ESC_RESET,
        'cflag': lambda val : ESC_CYAN + val[:2] + ESC_RESET + val[2:],
        'include': lambda val : ESC_CYAN + val[:2] + ESC_RESET + ESC_BLUE + ESC_UNDERLINE + val[2:] + ESC_RESET
}


@dataclass
class ExecArgument:
    """
    Argument string with attached note for formatter to print this arg.
    """

    value : Any
    """Value of the argument, passed to executable"""

    fmt : FormatterName 
    """Name of the formatter to use when coloring this argument"""

    def __str__(self) -> str:
        return str(self.value)


class ExecBuildStep(BuildStep):
    """
    Step of build process which executes some command.

    There is `input_files` property. `input_version` by
    default combines `getmtime()` of all of them into `input_version`.
    Also it is used when generating `compile_commands.json`.

    """

    def __init__(self, command : str, dependencies=[], args : list = []) -> None:
        super().__init__(dependencies)
        self.command = command
        self.args = list(args)

    @property
    def input_files(self) -> list[Path]:
        """
        List of files this step depends on.
        Used when generating `compile_commands.json`.
        """
        return []

    def _print_command(self):
        """
        Print command of this step into TTY, wrapping and
        formatting flags.
        """
        print(CMD_PREF + ESC_BOLD + self.command + ESC_RESET)

        lines = [CMD_ARGS_PREF]
        line_w = 0

        for arg in self.args:
            arg_str = FORMATTERS[arg.fmt](str(arg.value)) if isinstance(arg, ExecArgument) else str(arg)
            if line_w + 1 + len(arg_str) > BEST_LINE_WIDTH:
                lines.append(CMD_ARGS_PREF)
                line_w = 0
            lines[-1] += arg_str + ' '
            line_w += len(arg_str) + 1

        for arg_str in lines:
            print(arg_str)
        print()


    async def run(self):
        self._print_command()

        async def reprint_stream(stream):
            async for line in stream:
                print(line.decode())

        process = await asyncio.subprocess.create_subprocess_exec(
                self.command, *map(str, self.args),
                stdout = subprocess.PIPE, stderr = subprocess.PIPE
        )

        await asyncio.wait([
            asyncio.create_task(reprint_stream(process.stdout)),
            asyncio.create_task(reprint_stream(process.stderr))
        ])

        # Some space after output
        print()

        if process.returncode != 0:
            print(f'{ESC_RED}Process returned exit code {process.returncode}, build failed{ESC_RESET}')
            print() # More space!
            self.fail()


    @property
    def step_id(self) -> str:
        return 'BuildExecStep ' + json.dumps([self.command] + list(map(str, self.args)))

    @property
    def input_version(self) -> str:
        return json.dumps([os.path.getmtime(i) for i in self.input_files])


def generate_compile_commands(last_steps : list[BuildStep], output : Path, directory : Path):
    """
    Generate `compile_commands.json` file, used by tools such as `clangd`
    to determine how file will be compiled. 

    Only `BuildExecStep`-s are written. For them to be written they must
    have one input file (property `input_files`).

    """
    res = []

    def generate(step : BuildStep):
        nonlocal file

        if not isinstance(step, ExecBuildStep):
            return # Cannot put non-command step into compile COMMANDS

        if len(step.input_files) != 1:
            return # Compile commands requires one file transformations.

        res.append({
            'directory': str(directory),
            'file': str(step.input_files[0]),
            'arguments': [step.command, *map(str, step.args)]
        })

    walk_deps(last_steps, generate) 

    with open(output, 'w') as file:
        json.dump(res, file, indent=2)

