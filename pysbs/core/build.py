__all__ = ['build']

from pysbs.core.step import BuildStep
from alive_progress import alive_bar
import traceback


ESC_GRAY = '\x1b[90m' #]
ESC_RESET = '\x1b[0m' #]
HEADER_PREFIX = '----[ ' #]
HEADER_SUFFIX = ' ]' 
HEADER_LEN = 80

BUILD_FAILED_MSG = '\n\nBuild failed'

def print_hader(name : str):
    print()
    filler_len = HEADER_LEN - len(HEADER_PREFIX) - len(HEADER_SUFFIX)
    print(ESC_GRAY + HEADER_PREFIX + ESC_RESET + 
          name +
          ESC_GRAY + HEADER_SUFFIX + '-' * filler_len + ESC_RESET)
    print()

class BuildError(Exception):
    pass

class BuildManager:

    # TODO: generate compile_commands

    def __init__(self, last_step : 'BuildStep') -> None:
        self.last_step = last_step
        self.to_update = []

    def build(self):
        self.to_update = []
        self._make_update_list(self.last_step)

        try:
            with alive_bar(len(self.to_update), enrich_print=False) as bar:

                def set_step_name(name : str):
                    print_hader(name)
                    bar.text(name)

                for i in self.to_update:

                    i._name_hook = set_step_name 
                    self._run(i)
                    i._name_hook = None
                    bar()
        except BuildError:
            print(BUILD_FAILED_MSG)


    def _make_update_list(self, step : 'BuildStep'):
        for i in step.dependencies:
            self._make_update_list(i)

        if step.input_version != step.last_time_input_version or step.did_fail_last_time:
            self.to_update.append(step)

    def _run(self, step : 'BuildStep'):
        if step.input_version != step.last_time_input_version:
            step._bump_version()
            try:
                step.run()
            except Exception as ex:
                step.print(traceback.format_exc())
                step.fail()
                raise BuildError()
        elif step.did_fail_last_time:
            print(step.last_time_fail_message)
            raise BuildError()
        else:
            raise RuntimeError('Cannot determine why this was ran...')

         



def build(last_step : 'BuildStep'):
    BuildManager(last_step).build()
