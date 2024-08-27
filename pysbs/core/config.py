import shelve

def escape_key(key : str):
    return key.replace('\\', '\\\\').replace('|', '\\|')



def get_database() -> shelve.Shelf:
    raise NotImplementedError # FIXME

