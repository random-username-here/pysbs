__all__ = ["BuildStep"]

from typing import Type, Callable, Optional
from . import config

# Version returned by 

class _BuildStepMetaclass(type):
    """
    Metaclass to give same instance of `BuildStep` if it
    is created twice.
    """

    def __call__(self : Type['BuildStep'], *args, **kwargs):
        step = self.__new__(self, *args, **kwargs) 
        step.__init__(*args, **kwargs)

        if step.step_id not in self.by_id:
            step.__postinit__()
            self.by_id[step.step_id] = step

        return self.by_id[step.step_id]

    def __init__(self, name, bases, attributes):
        super().__init__(name, bases, attributes)
        self.by_id = {}


class BuildStep(metaclass=_BuildStepMetaclass):
    """
    Compilation is separated into steps - you compile one
    file, another, link them together, etc.. This class is 
    used to represent such steps.

    Each step can have dependencies (like linking step may depend
    on compilation step), has some way to check if files/other things
    it depends on changed.

    When you create a new instance of this class, its hash is checked in
    dict to see if it is a duplicate. If it is, you will be given already
    created one.

    TODO: clean db from unused steps
    """

    by_id : dict[str, 'BuildStep']
    """Class property, containing all created steps by their id"""

    dependencies : list['BuildStep']
    """List of steps this one depends on"""

    __m_name : str
    __m_name_hook : Optional[Callable[[str], None]]
    __m_ns : config.PersistentNamespace
    __m_captured_output : str

    INPUT_VERSION_NOT_EXISTENT = ''
    """Version returned when this step data did not exist on previous run"""

    ### User-defined methods ###############################

    @property
    def step_id(self) -> str:
        """
        Something which can be used to differentiate this
        step from other steps.
        """
        raise NotImplementedError

    @property
    def input_version(self) -> str:
        """
        Some string you use to pin input versions for things
        like files. So if this string changes from previous
        check, it means some file changed, and you need to
        rebuild.
        """
        raise NotImplementedError

    def run(self):
        """
        Run this step. Compile/link/generate something here.
        """
        pass

    ### Internal methods ###################################

    def __init__(self, dependencies = []) -> None:
        self.__m_name = ""
        self.__m_name_hook = None
        self.__m_captured_output = ''
        self._failed = False
        self.dependencies = list(dependencies)

    def __postinit__(self):
        self.__m_ns = config.get_database().get_ns('steps').get_ns(self.step_id)

    @property
    def name(self):
        return self.__m_name

    @name.setter
    def name(self, v : str):
        self.__m_name = v
        if self._name_hook != None:
            self._name_hook(v)

    @property
    def _name_hook(self):
        return self.__m_name_hook

    @_name_hook.setter
    def _name_hook(self, hook):
        self.__m_name_hook = hook
        if hook is not None:
            hook(self.name)

    @property
    def ns(self):
        """Namespace for storing data of this step."""
        return self.__m_ns

    def fail(self):
        """
        Make this step fail.
        All output of this step is saved, and will be
        printed next time build will be run without this
        inputs changing.
        """
        self.ns['has_failed'] = True
        self.ns['fail_message'] = self.__m_captured_output
        self._failed = True

    def print(self, *vals, sep=' ', end='\n'):
        """
        Print something.
        This output is captured and printed again if this
        step failed previous time, and nothing changed.
        """
        print(*vals, sep=sep, end=end)
        self.__m_captured_output += str(sep).join(map(str, vals)) + end

    @property
    def last_time_input_version(self) -> str:
        """
        Input version this was run last time with
        """
        return self.ns.get('last_time_input_version', self.INPUT_VERSION_NOT_EXISTENT)

    @property
    def did_fail_last_time(self) -> bool:
        """
        Did this step fail last time it was run?
        """
        return self.ns.get('has_failed', False)

    @property
    def last_time_fail_message(self):
        return self.ns.get('fail_message', '')

    def _bump_version(self):
        """
        Update last input version.
        """
        self.ns['last_time_input_version'] = self.input_version

    def _reset_error(self):
        """
        Reset error stored in persistent storage
        """
        self.ns['has_failed'] = False
        self.ns['fail_message'] = ''
        self._failed = False

class Foo(BuildStep):
    pass
