import re, inspect, sys
from colorama import Fore
from typing import Any, Dict, Literal, Set, Tuple, Callable
from types import ModuleType


def get_file_type(filename: str) -> Literal['yaml', 'json', 'excel']:
    if re.search(r'[^.]*\.(yaml|yml)$', filename):
        return 'yaml'
    elif re.search(r'[^.]*\.json$', filename):
        return 'json'
    elif re.search(r'[^.]*\.xlsx?$', filename):
        return 'excel'
    
    return None


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


def get_total_size(obj, seen=None):
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    if isinstance(obj, dict):
        size += sum([get_total_size(k, seen) + get_total_size(v, seen) for k, v in obj.items()])
    elif isinstance(obj, (list, tuple, set)):
        size += sum([get_total_size(i, seen) for i in obj])
    
    return size


def split_seconds(seconds) -> Tuple[int, int, int]:
    hh = seconds // 3600
    mm = (seconds % 3600) // 60
    ss = seconds % 60

    return (hh, mm, ss)


def format_seconds(seconds: int) -> str:
    hh, mm, ss = split_seconds(seconds)

    return f'{hh:02}:{mm:02}:{ss:02}'


def format_size(size: int) -> str:
    kb: int = 1024
    mb: int = kb * kb
    sz: float = size
    unit: str = 'B'

    if size >= mb:
        sz = round(size/mb, 2)
        unit = 'MB'
    elif size >= kb:
        sz = round(size/kb, 2)
        unit = 'KB'

    if sz != 1.00: unit += 's'

    return f'{sz} {unit}'


def portal_action(name: str, config: Dict | bool, portal_module: ModuleType) -> Callable:
    try:
        if portal_module:
            fn = getattr(portal_module, name)
        elif type(config.get('portal', False)) is dict:
            fn = config['portal'][name]

        args_count = count_required_args(fn)

        return fn, args_count
    except Exception:
        raise ValueError(Fore.RED + 'Unsupported portal action, ' + Fore.CYAN + name + Fore.RESET)