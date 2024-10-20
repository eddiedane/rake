import re
from typing import Dict, List, Literal, Tuple
from colorama import Fore


ParseValueData = Dict[Literal['prop', 'child_node', 'ctx', 'selector', 'max', 'utils', 'parsed_utils', 'var'], int | str | List | None]
KeyMatchData = Dict[Literal['is_left_var', 'left_operand', 'operator', 'is_right_var', 'right_operand'], str]


def parse_value(string: str, set_defaults: bool = True) -> ParseValueData:
    """
    Parse a value notation string into its parts.

    The format of the string is as follows:
    [prop[:child(n)]]@[<page|parent>[.all|first]>selector[|utils >> var]

    Where:
    - prop is the name of the property to get (e.g. 'text', 'attr', etc.)
    - child(n) is an optional child node index to get (e.g. 'child(0)')
    - page|parent is an optional context to get the selector from (e.g. 'page', 'parent')
    - all|first is an optional maximum number of nodes to get (e.g. 'all', 'first')
    - selector is the selector to get (e.g. 'h1', 'div.title')
    - utils is an optional list of utilities to apply to the value (e.g. 'trim', 'lowercase', etc.)
    - var is an optional variable name to assign the result to (e.g. 'title')

    The function returns a dictionary with the following keys:
    - prop: the name of the property to get
    - child_node: the child node index to get (if any)
    - ctx: the context to get the selector from (page or parent)
    - max: the maximum number of nodes to get (all or first)
    - selector: the selector to get
    - utils: the list of utilities to apply to the value
    - parsed_utils: the parsed list of utilities
    - var: the variable name to assign the result to (if any)

    If set_defaults is True, the function will set default values for the keys
    that are not present in the input string.
    """
    
    value_re = r'(?:(?P<prop>\w+)(?::child\((?P<child_node>\d+)\))?)\s*(?:@\s*(?:<(?P<ctx>page|parent)(?:\.(?P<max>all|one))?>)?(?P<selector>[^|<]+))?(?:\s*\|\s*(?P<utils>\w+(?:\s+[^>]+)*))*\s*(?:>>\s*(?P<var>\w+))?'
    match = re.fullmatch(value_re, string)

    if not match:
        return {'prop': None, 'ctx': None, 'selector': None, 'utils': None, 'parsed_utils': []}
    
    data: ParseValueData = match.groupdict()
    
    if set_defaults:
        data['prop'] = (data['prop'] or '').strip()
        data['child_node'] = int(data['child_node']) if data['child_node'] else None
        data['selector'] = (data['selector'] or '').strip()
        data['utils'] = (data['utils'] or '').strip()
        data['ctx'] = data['ctx'] or 'parent'
        data['max'] = data['max'] or 'one'

    if not data['utils']:
        data['parsed_utils'] = []

        return data
    
    utils = re.split(r'\s*\|\s*', data['utils'])
    parsed_utils = []

    for util in utils:
        util_parts = re.split(r'\s+', util.strip())
        parsed_utils.append((util_parts[0], util_parts[1:]))

    data['parsed_utils'] = parsed_utils

    return data


def parse_getters(string: str) -> List[Tuple[str, str, str]]:
    """
    Returns a set of tuples containing the full match, the getter type (var or attr) and the getter value.
    
    Args:
        string (str): The string to search for getters.
    
    Returns:
        List[Tuple[str, str, str]]: A set of tuples containing the full match, the getter type and the getter value.
    """
    return set(re.findall(r'(\$(var|attr)\{\s*([^|}]+(?:\s*\|\s*\w+(?:\s+[^\s{}]+)*)*\s*)\})', string))


def find_item_key(key, value, vars):
    """
    Returns the key of an item in a given value that matches a given comparison string.

    The comparison string should be of the form "$key{<left_operand> <operator> <right_operand>}",
    where <left_operand> and <right_operand> are strings that represent keys in the items of the given value,
    and <operator> is one of "=", "!=", ">=", "<=", ">", "<".

    If the given value is a dict, this function will return the key of the item where the comparison is true.
    If the given value is a list, this function will return the index of the item where the comparison is true.
    If the given value is neither a dict nor a list, this function will raise a TypeError.

    If no item matches the comparison, this function will raise a ValueError.

    Args:
        key (str): The comparison string.
        value (dict | list): The value to search for the item.
        vars (dict): A dictionary of variables, where the keys are the variable names and the values are the variable values.

    Returns:
        str | int: The key of the item that matches the comparison.
    """
    key_re = r'\$key\{\s*(?P<is_left_var>\$)?(?P<left_operand>\w+)\s*(?P<operator>=|!=|>=|<=|>|<)\s*(?P<is_right_var>\$)?(?P<right_operand>\w+)\s*\}'
    match = re.search(key_re, key)

    if not match: return key

    match_data: KeyMatchData = match.groupdict()
    operator = match_data['operator']
    left_operand = vars[match_data['left_operand']] if match_data['is_left_var'] else match_data['left_operand']
    right_operand = vars[match_data['right_operand']] if match_data['is_right_var'] else match_data['right_operand']

    if type(value) is dict: items = value.items()
    elif type(value) is list: items = enumerate(value)
    else: raise TypeError(Fore.RED + f'Invalid operation type (dict and list only) at ' + Fore.CYAN + key + Fore.RESET)

    for k, v in items:
        found = False

        match operator:
            case '=': found = v[left_operand] == right_operand
            case '!=': found = v[left_operand] != right_operand
            case '>=': found = v[left_operand] >= right_operand
            case '<=': found = v[left_operand] <= right_operand
            case '>': found = v[left_operand] > right_operand
            case '<': found = v[left_operand] < right_operand
            case _: raise ValueError(Fore.RED + 'Invalid operator ' + Fore.CYAN + operator + Fore.RED + ' at ' + Fore.CYAN + key + Fore.RESET)
        
        if found: return k
    else:
        raise ValueError(Fore.RED + 'No match found at ' + Fore.CYAN + key + Fore.RED + ' with comparsion of ' + Fore.BLUE + f'{left_operand}{operator}{right_operand}' + Fore.RESET)
    