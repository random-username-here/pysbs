from collections.abc import Callable
from pysbs.core.step import BuildStep

def walk_deps(end_steps : list[BuildStep], callable : Callable[[BuildStep], None]):
    """
    Walk dependencies of given steps (including those steps), executing callable
    for each of them once. Dependencies are handled before steps which depend on
    them.
    """

    visited = set()

    def visit(step : BuildStep):

        if hash(step.step_id) in visited:
            return
        visited.add(hash(step.step_id))

        for i in step.dependencies:
            visit(i)

        callable(step)

    for i in end_steps:
        visit(i)
