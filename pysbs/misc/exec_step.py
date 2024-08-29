from collections.abc import Callable
import os
import subprocess
from typing import Any, Literal
from pysbs.core.step import BuildStep
import asyncio.subprocess
import select
import json
from dataclasses import dataclass

ESC_GRAY = '\x1b[90m' #]
ESC_RESET = '\x1b[0m' #]
ESC_BOLD = '\x1b[1m' #]
ESC_RED = '\x1b[91m' #]
ESC_BLUE = '\x1b[94m' #]
ESC_GREEN = '\x1b[92m' #] for paths
ESC_UNDERLINE = '\x1b[4m' #] for paths

BEST_LINE_WIDTH = 120

CMD_PREF = f'{ESC_GRAY} $ {ESC_RESET}'
CMD_ARGS_PREF = f'{ESC_GRAY} :   {ESC_RESET}'

FormatterName = Literal['normal', 'path', 'cflag', 'include']

FORMATTERS : dict[FormatterName, Callable[[str], str]] = {
        'normal': lambda s : s,
        'path': lambda path : ESC_GREEN + ESC_UNDERLINE + path + ESC_RESET,
        'cflag': lambda val : ESC_BLUE + val[:2] + ESC_RESET + val[2:],
        'include': lambda val : ESC_BLUE + val[:2] + ESC_RESET + ESC_GREEN + ESC_UNDERLINE + val[2:] + ESC_RESET
}

@dataclass
class ExecArgument:
    value : Any
    fmt : FormatterName 

    def __str__(self) -> str:
        return str(self.value)

class ExecBuildStep(BuildStep):
    """
    Step of build process which executes some command.

    You must define `input_version` yourself.
    """


    def __init__(self, command : str, dependencies=[], args : list = []) -> None:
        super().__init__(dependencies)
        self.command = command
        self.args = list(args)


    def _print_command(self):
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
