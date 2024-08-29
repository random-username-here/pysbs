"""
Parser to extract list of includes (or imports, or whatever) from given source.
"""

__all__ = ['find_includes']

from dataclasses import dataclass
import re
from typing import Optional


@dataclass
class ExcludedZoneSpec:
    """
    Sppecification about excluded zone - part of file in which
    we do not search for includes, even if there can be syntax
    we want. Like comment or string - we do not search for includes
    there, even if there is `#include` in them.

    FIXME: `{` and `}` in strings for Python's new f-strings
    """

    begin : str;
    """Word from which excluded zone begins, for example `/*` for block comment"""

    end : str;
    """Word after which excluded zone ends, for example `*/` for block comment"""

    has_escapes : bool = False;
    """If true, we can escape end symbols in that zone. It is true for strings, false for comments"""

    is_ignored_by_parser: bool = False;
    """
    If true, this excluded zone is ignored by compiler/interpreter.
    So, if it is `True` and we are searching for `#include` at the
    beginning of the line, after this zone we will still think this is
    the beginning of the line.
    
    For example, this: 
    ```c
    /* my comment */ #include "foobar.h"
    ```
    
    will be found, but this:

    ```c
    "my string" #include "foobar.h"
    ```

    will be ignored.
    """

# Character used to escape character following it
ESCAPE_CHAR = '\\'

# Escape codes for debug listing
EXCLUDED_ZONE_HIGHLIGHT = '\x1b[90m' #]
RESET_HIGHLIGHT = '\x1b[0m' #]
MATCH_HIGHLIGHT = '\x1b[91m' #]
LINE_BEGIN_MARKER_HIGHLIGHT = '\x1b[91m' #] Red color

# Marker to be printed at the place, where matcher will be run.
LINE_BEGIN_MARKER = '♦'


def exl_print(c : str):
    """Print some text in excluded zone highlight. For debug listing."""
    print(EXCLUDED_ZONE_HIGHLIGHT + c + RESET_HIGHLIGHT, end='') #]]

def has_substring(src : str, pos : int, substr : str):
    """Check if given string has given substring from `pos` to `pos + len(substr)`"""
    if len(src) < pos + len(substr):
        return False
    for i in range(len(substr)):
        if src[pos+i] != substr[i]:
            return False
    return True

def find_includes(source : str,
                  excluded_zones : list[ExcludedZoneSpec],
                  matcher : re.Pattern,
                  has_nl_escapes : bool = True,
                  debug : bool = False):
    """
    Find includes, imports or whatever in given file.

    Paramters
    ---------
    source
        Source file contents, in which we look for includes/imports

    excluded_zones
        List of `ExcludedZoneSpec`-s, which specify zones,
        in which we do not search for includes/imports.
        Strings and comments are examples of such zones.

    matcher
        Regex pattern which matches include/import directive.
        This will be ran only on start if the lines
        (code after comments still counts as at the start of the line)

    has_nl_escapes
        If `True`, we can continue string to next line using `\\` symbol
        at the end of the line. Spaces after it and befor end of the line
        are ignored.

    debug
        If `True`, this function will print listing of given source,
        with excluded zones and matches highlighted, line start positions
        marked.
    """

    pos = 0                                  # Location in source code
    zone : Optional[ExcludedZoneSpec] = None # Spec of current excluded zone
    escape = False                           # Is next symbol escaped?
    on_line_begin = True                     # Are the at the beginning of the line?
    possible_escape_nl = False               # Will next \n be escaped?
    result = []                              # Array with all the matches, which
                                             # will be returned

    if debug:
        # Make some space around listing
        print()

    while pos < len(source):
        if zone:
            # We are in excluded zone
            if debug:
                # Print current char
                exl_print(source[pos])

            if escape: 
                # This symbol was escaped, continue
                escape = False
                pos += 1
                continue
            
            elif zone.has_escapes and source[pos] == ESCAPE_CHAR:
                # Escape next symbol
                escape = True
                pos += 1
                continue

            elif has_substring(source, pos, zone.end):
                # End of the zone
                
                if debug:
                    # Print it!
                    exl_print(source[pos+1:pos+len(zone.end)])

                pos += len(zone.end)
                if zone.end[-1] == '\n':
                    # Zone ends at '\n', new line starts
                    on_line_begin = True
                zone = None
            
            else:
                # Normal symbol, just advance
                pos += 1
        else:
            for i in excluded_zones:
                if has_substring(source, pos, i.begin):
                    # Begin new zone!

                    if debug:
                        exl_print(source[pos:pos+len(i.begin)])
                    
                    zone = i
                    pos += len(i.begin)
                    on_line_begin = on_line_begin and zone.is_ignored_by_parser
                    possible_escape_nl = False

                    break
            else:
                # Zone did not begin...
                if has_nl_escapes and source[pos] == ESCAPE_CHAR:
                    # Newline escape (if this language has them)
                    possible_escape_nl = True
                
                if source[pos] == '\n':
                    # Non-escaped newline
                    if not possible_escape_nl:
                        on_line_begin = True
                    possible_escape_nl = True
                
                elif not source[pos].isspace():
                    # Not a space

                    if on_line_begin:
                        # Test for include here

                        if debug:
                            # Print marker
                            print(LINE_BEGIN_MARKER_HIGHLIGHT + LINE_BEGIN_MARKER + RESET_HIGHLIGHT, end='') #]]
                        
                        match = re.match(matcher, source[pos:]) 
                        
                        if match:
                            # We matched include

                            if debug:
                                print(MATCH_HIGHLIGHT + match.group(0) + RESET_HIGHLIGHT, end='')
                            
                            result.append(match)
                            pos += len(match.group(0))
                            on_line_begin = False
                            possible_escape_nl = False
                            
                            continue

                    on_line_begin = False

                    if source[pos] != ESCAPE_CHAR:
                        possible_escape_nl = False
                
                if debug:
                    print(source[pos], end='')
                
                pos += 1

    if debug:
        print()

    return result


if __name__ == '__main__':

    # Usage example
    matches = find_includes(open(__file__, 'r').read(), [
        # Comments
        ExcludedZoneSpec(begin='#', end='\n', is_ignored_by_parser=True),
        # Docstrings
        ExcludedZoneSpec(begin='"""', end = '"""', has_escapes=True),
        ExcludedZoneSpec(begin='\'\'\'', end = '\'\'\'', has_escapes=True),
        # Normal strings
        ExcludedZoneSpec(begin='\'', end = '\'', has_escapes=True),
        ExcludedZoneSpec(begin='"', end = '"', has_escapes=True),
    ], re.compile(r'(?:from ([^\s\n]+) import )|(?:import ([^\s\n]+))'), debug=True)

    # Extract match from regex
    includes = [ list(filter(bool, i.groups()))[0] for i in matches ]
    
    print('This file depends on', includes)
