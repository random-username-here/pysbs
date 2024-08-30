from collections.abc import Callable

from alive_progress.core.hook_manager import logging
from pysbs.core.step import BuildStep
from pysbs.misc.walk import walk_deps

def ghash(v):
    return 'n_' + str(hash(v)).replace('-', 'm')

def make_dot_graph(top_steps : list[BuildStep],
                   fmt : Callable[[BuildStep], str] = lambda v : v.step_id,
                   extra_graph_data : str = '',
                   extra_note_attrs : Callable[[BuildStep], list[str]] = lambda _ : []):
    """
    Generate graph of step dependencies in DOT format to be
    rendered by graphviz

    fmt takes step, should return label to show.
    """

    result = ""

    def add_step(s : BuildStep):
        nonlocal result

        logging.debug(f'Generating DOT node for {s.step_id}')

        params = [f'label="{fmt(s)}"', *extra_note_attrs(s)]
        result += f'  {ghash(s.step_id)} [{', '.join(params)}];\n'

        for i in s.dependencies:
            result += f'  {ghash(i.step_id)} -> {ghash(s.step_id)};\n'

    result += "digraph build_tree {\n" #}
    result += extra_graph_data + '\n'

    walk_deps(top_steps, add_step)

    result += "}\n"

    return result
