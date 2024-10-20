import re, inspect
from typing import Any, Dict, List, Literal, Set


def is_file_type(typ: Literal['yaml', 'json'], filename: str) -> bool:
    """
    Checks if a given filename matches a specific file type.

    Parameters
    ----------
    typ : Literal['yaml', 'json']
        The type of file to check.
    filename : str
        The name of the file to check.

    Returns
    -------
    bool
        True if the filename matches the given type, False otherwise.
    """

    if re.search(r'[^.]*\.(yaml|yml)$', filename) and typ == 'yaml':
        return True
    elif re.search(r'[^.]*\.json$', filename) and typ == 'json':
        return True
    
    return False


def pick(obj: Dict, key_map: Set | Dict[str, str] = {}) -> Dict:
    """
    Selectively pick a subset of keys from given dictionary into a new
    dictionary. If key_map is a set, it is treated as a set of keys to pick,
    and the resulting dictionary will use the same key names. If key_map is
    a dictionary, the keys in obj will be remapped to the corresponding values
    in key_map.

    Args:
        obj (Dict): The dictionary to pick from
        key_map (Set | Dict[str, str], optional): The set of keys or dictionary of key mappings.
            Defaults to {}.

    Returns:
        Dict: The resulting dictionary with the picked keys
    """

    _obj = {}
    
    if type(key_map) is set:
        _key_map = {}

        for key in key_map: _key_map[key] = key

        key_map = _key_map


    keys = [] if not key_map else key_map.keys()

    for key, value in obj.items():
        if key not in keys: continue
        
        key = key_map[key]
        _obj[key] = value

    return _obj
        

def is_numeric(val: Any) -> bool:
    """
    Checks if given value can be converted to a float.

    Args:
        val (Any): The value to check.

    Returns:
        bool: True if the value can be converted to a float, False otherwise.
    """
    
    try:
        float(val)
        return True
    except:
        return False
    

def count_required_args(func):
    """
    Counts the number of required arguments in a function.

    Args:
        func: The function to inspect.

    Returns:
        int: The number of required arguments.
    """
    
    # Get the signature of the function
    sig = inspect.signature(func)
    # Count the number of required arguments
    required_args = sum(
        1 for param in sig.parameters.values()
        if param.default == inspect.Parameter.empty and
           param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.KEYWORD_ONLY)
    )
    
    return required_args


def is_none_keys(obj: Dict, *keys) -> bool:
    """
    Checks if all given keys in the object are None.

    Args:
        obj (Dict): The object to check.
        *keys: The keys to check.

    Returns:
        bool: True if all given keys are None, False otherwise.
    """
    
    for key in keys:
        if key in obj and obj[key] is not None: return False
    
    return True