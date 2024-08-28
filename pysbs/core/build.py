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
        self.update_ids = set()

    def build(self):

        self.make_update_list()

        if len(self.to_update) == 0:
            print('All up to date')
            return

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


    def make_update_list(self):
        self.to_update = []
        self.update_ids = set()
        self._make_update_list(self.last_step)


    def _make_update_list(self, step : 'BuildStep') -> bool:

        any_deps_changed = False

        for i in step.dependencies:
            this_changed = self._make_update_list(i)
            any_deps_changed = any_deps_changed or this_changed

        if (any_deps_changed or
                step.input_version != step.last_time_input_version or
                step.did_fail_last_time) and step.step_id not in self.update_ids:
            self.to_update.append(step)
            self.update_ids.add(step.step_id)
            return True
        return False

    def _run(self, step : 'BuildStep'):
        if step.did_fail_last_time:
            print(step.last_time_fail_message)
            raise BuildError()
        else:
            step._bump_version()
            step._reset_error()
            try:
                step.run()
            except Exception as ex:
                step.print(traceback.format_exc())
                step.fail()
        
            if step._failed:
                raise BuildError()



def build(last_step : 'BuildStep'):
    BuildManager(last_step).build()
