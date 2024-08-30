# Add project folder to path
import sys
from pathlib import Path


THIS_FILE = Path(__file__)
sys.path.append(str(THIS_FILE.parent.parent.parent))

from pysbs.core.step import BuildStep
from pysbs.c.project import CProject
from pysbs.c.deps import CDependencyStep
from pysbs.core.config import use_database
from pysbs.misc.graphviz import make_dot_graph
from pathlib import Path

import logging, coloredlogs
coloredlogs.install(level=logging.DEBUG)

use_database(THIS_FILE.parent / 'pysbs.db')

# ---- Change this part ------------------------------------

# Path to some C project with a lot of files
PATH = Path('/home/i-s-d/code/mipt-sqr-calculator/')

INCLUDE_PATHS = [
    # Paths to resolve includes from
    PATH / 'include'
]

SOURCES = [
    # List of source files, to search includes from
    *((PATH / 'src').glob('**/*.c')),
    *((PATH / 'test').glob('**/*.c')),
    *((PATH / 'demos').glob('**/*.c')),
]

# ---- End of changed part ---------------------------------

if not PATH.exists:
    logging.fatal('You should change location of C project in this demo for it to work.')

proj = CProject()
proj.include_paths += INCLUDE_PATHS

logging.info('Resolving includes')

steps = [ CDependencyStep(proj, i) for i in SOURCES ]

logging.info('Making DOT graph')



def get_node_label(step : BuildStep):
    # Function wihci returns label for graph node based on step
    name = step.step_id.split('{')[1].split('}')[0].strip().removeprefix(str(PATH) + '/')

    if name.startswith('test/'):
        return '󰙨 ' + name
    elif name.startswith('include/'):
        return '\ueb9c ' + name
    elif name.startswith('src/'):
        return '\ue61e ' + name

    return name

def get_node_props(step : BuildStep):
    if 'demos/' in step.step_id:
        return ['penwidth=3']
    return []

EXTRA_DOT = """
layout=dot;
overlap=false;
node[fontname="CaskaydiaCove Nerd Font"];
node[shape=box];
rankdir=LR;
"""

dot = make_dot_graph(steps, fmt=get_node_label, extra_graph_data=EXTRA_DOT, extra_note_attrs=get_node_props)

open(THIS_FILE.parent / 'graph.dot', 'w').write(dot)

