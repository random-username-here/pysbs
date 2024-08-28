import shelve
from typing import Any, Optional
import os

def _esc(key : str):
    """
    Escape string to use it as key in storage.
    Storage is hierarchical, but backend is not.
    So we concat path using `|`, but then `|`-s in keys
    must be escaped.
    """
    return key.replace('\\', '\\\\').replace('|', '\\|')

# Shelf where we put persistent data
dbfile : Optional[shelve.Shelf] = None

def use_database(file : os.PathLike):
    """
    Use file at given path to store all data between
    compilations.
    """
    global dbfile
    dbfile = shelve.open(file)

def get_database() -> 'PersistentNamespace':
    """
    Get root namespace of the database
    """
    if dbfile is None:
        raise RuntimeError("Database file was not opened! Use `use_database()` to that")
    return PersistentNamespace(dbfile, '')

class PersistentNamespace:
    """
    Namespaces are like folders, in which you can have
    more namespaces (like folders) and keys (like files).
    Actually they are stored as `path -> value` pairs, so
    all this structure is abstraction.
    """

    def __init__(self, db : shelve.Shelf, ns : str) -> None:
        self.db = db
        self.prefix = ns

    def get_ns(self, name : str) -> 'PersistentNamespace':
        """Get subnamespace of this"""
        return PersistentNamespace(self.db, self.prefix + '|' + _esc(name))

    def __getitem__(self, name : str):
        return self.db[self.prefix + '|' + _esc(name)]

    def get(self, name : str, default : Any = None):
        return self.db.get(self.prefix + '|' + _esc(name), default)

    def __setitem__(self, name : str, val : Any):
        self.db[self.prefix + '|' + _esc(name)] = val
        self.db.sync()
