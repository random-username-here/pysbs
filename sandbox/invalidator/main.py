from pathlib import Path
import sys

THIS_FILE = Path(__file__)
THIS_FOLDER = THIS_FILE.parent
sys.path.append(str(THIS_FILE.parent.parent.parent))
##### Begin build code

import logging
from pysbs.misc.invalidator import DeptreeFile, make_python_deptree

logging.basicConfig(level=logging.DEBUG)

tree = make_python_deptree(THIS_FOLDER.parent / 'cproject' / 'build.py')

graph = """digraph G {
    rankdir=LR;
    layout=dot;
    overlap=false;
    node[fontname="CaskaydiaCove Nerd Font"];
    node[shape=box];
"""


visited = set()

def node_name(node):
    return 'n_' + str(hash(node.path)).replace('-', 'm')

def visit(node : DeptreeFile):
    global graph    

    if node.path in visited:
        return
    visited.add(node.path)

    graph += f'    {node_name(node)} [label="{node.modname}"];\n'

    for i in node.deps:
        visit(i)
        graph += f'    {node_name(node)} -> {node_name(i)};\n'

visit(tree)

graph += '}\n'

(THIS_FOLDER / 'deps.dot').write_text(graph)
