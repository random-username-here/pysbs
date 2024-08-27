__all__ = ["BuildStep"]

from typing import Type, Callable, Optional
from . import config


class _BuildStepMetaclass(type):
    """
    Metaclass to give same instance of `BuildStep` if it
    is created twice.
    """

    def __call__(self : Type['BuildStep'], *args, **kwargs):
        step = self.__new__(self, *args, **kwargs) 
        step.__init__(*args, **kwargs)

        key = config.escape_key(step.step_id)

        if key not in self.by_id:
            self.by_id[key] = step

        return self.by_id[key]

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

    HACK: for now no persistency, because it is 20:30 and I want to see it run.
    """

    by_id : dict[str, 'BuildStep']
    """Class property, containing all created steps by their id"""

    dependencies : list['BuildStep']
    """List of steps this one depends on"""

    __m_name : str
    __m_name_hook : Optional[Callable[[str], None]]
    hidden : bool

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

    def __init__(self) -> None:
        self.__m_name = ""
        self.__m_name_hook = None
        self.hidden = False
        self.dependencies = []

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

    def fail(self):
        """
        Make this step fail.
        All output of this step is saved, and will be
        printed next time build will be run without this
        inputs changing.
        """
        return # HACK
        raise NotImplementedError

    def print(self, *vals, sep=' ', end='\n'):
        """
        Print something.
        This output is captured and printed again if this
        step failed previous time, and nothing changed.
        """
        print(*vals, sep=sep, end=end)
        return # FIXME: save output
        raise NotImplementedError

    @property
    def last_time_input_version(self) -> str:
        """
        Input version this was run last time with
        """
        return '' # HACK
        raise NotImplementedError

    @property
    def did_fail_last_time(self):
        """
        Did this step fail last time it was run?
        """
        return False # HACK
        raise NotImplementedError

    @property
    def last_time_fail_message(self):
        raise NotImplementedError

    def _bump_version(self):
        """
        Update last input version.
        """
        return # HACK
        raise NotImplementedError

class Foo(BuildStep):
    pass
