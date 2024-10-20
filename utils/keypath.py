import re
from utils.helpers import count_required_args
from typing import Any, Callable, Dict, List

def split(path: str, delimiter: str = '.') -> List[str]:
    """
    Splits a given path into an array of strings, using the given delimiter
    (defaulting to '.'). The path can contain square brackets, which are
    treated as a single delimiter. Any resulting consecutive
    delimiters will be collapsed into one.

    Args:
        path (str): The string to split into an array.
        delimiter (str): The string to split by. Defaults to '.'.

    Returns:
        List[str]: The resulting array of strings.
    """
    
    sanitized_path = re.sub(r'\]+$', '', path)
    sanitized_path = re.sub(r'[\[\]]+', delimiter, path)
    sanitized_path = re.sub(r'\.{2,}', delimiter, path)
    
    return sanitized_path.split(delimiter)


def get(path: str | List[str], obj: List | Dict, default: Any = None, delimiter: str = '.') -> Any:
    """
    Gets a value from an object by a given path.

    Args:
        path (str | List[str]): The path to the value. Can be a string or a list of strings.
        obj (List | Dict): The object to get the value from.
        default (Any, optional): The default value to return if the path does not exist. Defaults to None.
        delimiter (str, optional): The delimiter to use when splitting the path string. Defaults to '.'.

    Returns:
        Any: The value at the given path or the default value if the path does not exist.
    """

    if type(path) == str:
        path = split(path, delimiter)

    if not len(path): return default

    value = obj

    for key in path:
        if not (type(value) in [dict, list, str] and has_key(value, key)):
            return default
        
        value = value[key]

    return value


def assign(
    value: Any,
    obj: List | Dict,
    path: str | List[str],
    delimiter: str = '.',
    merge: bool = False
) -> List | Dict:
    """
    Assigns a value to a given path in an object. The path can be a string
    or a list of strings. If the path is a string, it will be split using
    the given delimiter (defaulting to '.'). If the path does not exist in
    the object, it will be created.

    Args:
        value (Any): The value to assign to the path.
        obj (List | Dict): The object to assign the value to.
        path (str | List[str]): The path to assign the value to.
        delimiter (str, optional): The delimiter to use when splitting the
            path string. Defaults to '.'.
        merge (bool, optional): If true, the value will be merged with the
            existing value instead of replacing it. Defaults to False.

    Returns:
        List | Obj: The object with the assigned value.
    """

    if type(path) == str:
        path = split(path, delimiter)
        
    _obj = obj
    size = len(path)
    if not size: return _obj

    for i, key in enumerate(path):
        if i == size - 1:
            if merge and has_key(_obj, key) and type(_obj[key] == type(value)):
                if type(value) in [str, int, list]:
                    _obj[key] += value
                elif type(value) == dir:
                    _obj[key] |= value
            else: _obj[key] = value
        else:
            _obj = _obj[key]

    return obj


def resolve(
    path: str | List[str],
    obj: List | Dict,
    vars: Dict = {},
    delimiter: str = '.',
    resolve_key: Callable = lambda k:k,
    strict: bool = False
) -> List:
    """
    Resolves a given path in an object,
    optionally replacing special keys using the given resolve_key function.
    
    Args:
        path (str|List[str]): The path to resolve in the object. Can be a string or a list of strings.
        obj (List|Dict): The object to resolve the path in.
        vars (Dict): The variables to replace in the path.
        delimiter (str): The delimiter to use when splitting the path string. Defaults to '.'.
        resolve_key (Callable): The function to use for resolving keys. Defaults to a lambda that simply returns the key.
        strict (bool): If true, raises a KeyError if the key is not found in the object. Defaults to False.
    
    Returns:
        List: The resolved path.
    """

    if type(path) == str:
        path = split(path, delimiter)
    
    if not len(path): return path

    resolved_path = []
    value = obj

    for i in range(len(path)):
        args_count = count_required_args(resolve_key)
        args = [path[i], value, vars, obj]

        if args_count > 4: args += [obj] * (args_count - 4)

        key = resolve_key(*args[0:args_count])
            
        if not ((type(value) is list or type(value) is dict) and has_key(value, key)):
            if strict: raise KeyError(f'Unable to resolve key "{key}"')
            else:
                resolved_path.append(key)
                continue

        value = value[key]
        resolved_path.append(key)

    return resolved_path


def has_key(obj: List | Dict | Any, key) -> bool:
    """
    Checks if a given key exists in an object.

    Args:
        obj (List|Dict|Any): The object to check.
        key (str|int): The key to check.

    Returns:
        bool: True if the key exists in the object, False otherwise.
    """
    
    if type(obj) in [list, str]:
        return key in dict(enumerate(obj))
    elif type(obj) is dict:
        return key in obj
    else:
        return hasattr(obj, key)
    

def to_string(keypath: List[str | int], delimiter: str = '.') -> str:
    """
    Converts a given keypath list into a string, using the given delimiter
    (defaulting to '.'). If the keypath contains integers, they will be
    wrapped in square brackets.

    Args:
        keypath (List[str|int]): The keypath list to convert.
        delimiter (str, optional): The delimiter to use between keys. Defaults to '.'.

    Returns:
        str: The resulting string.
    """

    _keypath = []

    for i, key in enumerate(keypath):
        if i == 0:
            _keypath.append(str(key))
            continue

        if type(key) is int: _keypath.append(f'[{str(key)}]')
        else: _keypath.append(delimiter + str(key))

    return ''.join(_keypath)
