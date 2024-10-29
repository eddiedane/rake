
import asyncio
from types import ModuleType
import re, json, os, importlib, time, shutil, random, string, yaml
from typing import Dict, Any, List, Literal, Tuple, Callable
from colorama import Fore, Style
from slugify import slugify
from tabulate import tabulate
import pandas as pd
from playwright.async_api import async_playwright, Browser, BrowserContext, BrowserType, Page, Locator, Route
from rake.utils.helpers import pick, is_none_keys, is_numeric, get_file_type, get_total_size, format_seconds, format_size
from rake.utils import notation, keypath, helpers as util


Config = Dict[Literal['browser', 'rake', 'output', 'logging', 'race'], Dict[str, Any] | bool]

PageConfig = Dict[Literal['link', 'interact'], str | Dict[str, Any]]

NodeConfig = Dict[Literal['element', 'all', 'range', 'links', 'data', 'interact', 'actions', 'wait', 'contains', 'excludes'], int | str | bool | List | Dict]

InteractConfig = Dict[Literal['repeat', 'nodes'], int | List[Dict[str, Any]] | Dict[str, Any]]

LinkConfig = Dict[Literal['name', 'url', 'metadata'], str | Dict[str, Any]]

DataConfig = Dict[Literal['scope', 'value'], str | List[str] | Dict[str, Any]]

ActionConfig = Dict[Literal['type', 'delay', 'wait', 'screenshot', 'dispatch', 'count'], str | int | bool]

Link = Dict[Literal['url', 'metadata'], str | Dict[str, Any]]

Links = Dict[str, List[Link]]

State = Dict[Literal['data', 'vars', 'links'], Dict[str, Any]]

Attribute = str | Dict[Literal['attribute', 'child_node', 'context', 'all', 'element', 'utils', 'var'], str | bool | List[str]]

DOMRect = Dict[Literal['x', 'y', 'width', 'height', 'top', 'right', 'bottom', 'left'], float]


class Rake:
    DEFAULT_LOGGING = False

    def __init__(self, config: Dict[str, Any] = {}):
        self.__browser_context: BrowserContext = None
        self.__browser: Browser = None
        self.__config = config
        self.__state: State = {'data': {}, 'vars': {}, 'links': {}}
        self.__start_time = 0
        self.__total_opened_pages = 0
        self.__id = ''.join(random.choices(string.ascii_letters + '_', k=6))
        self.__portal: ModuleType | None = None


    async def start(self) -> Dict:
        try:
            await self.__start()
            return self.data()
        except Exception as e:
            raise e
        finally:
            if self.__config.get('logging', Rake.DEFAULT_LOGGING):
                print()
                self.table()
                print()


    def data(self, filepath: str | List[str] = [], output: bool = False) -> Dict:
        if output:
            outputs = self.__get_outputs()

            if filepath:
                if type(filepath) is str:
                    filepath = [filepath]
                
                for path in filepath:
                    outputs.append({
                        'type': get_file_type(path),
                        'path': path,
                        'transform': None
                    })

            for output_config in outputs:
                self.__output(
                    output_config.get('path'),
                    output_config.get('type'),
                    transform=output_config.get('transform', None)
                )

        return self.__state['data']


    def links(self, filepath: str | None = None) -> Dict:
        if not filepath: 
            self.__output(filepath, get_file_type(filepath), state='links')

        return self.__state['links']


    def table(self) -> None:
        duration = format_seconds(int(time.time() - self.__start_time))
        data_size = format_size(get_total_size(self.__state['data']))
        mode = 'headless' if not self.__config.get('browser', {}).get('show', False) else 'visible'
        output = ', '.join([output['type'].upper() for output in self.__get_outputs()] or ['dict'])

        headers = [
            Style.BRIGHT + 'Crawled Pages' + Style.NORMAL,
            Style.BRIGHT + 'Mode' + Style.NORMAL,
            Style.BRIGHT + 'Duration' + Style.NORMAL,
            Style.BRIGHT + 'Data Size' + Style.NORMAL,
            Style.BRIGHT + 'Output' + Style.NORMAL
        ]

        rows = [[
            self.__total_opened_pages,
            mode,
            duration,
            data_size,
            output
        ]]

        print(tabulate(rows, headers, tablefmt="double_outline"))


    async def end(self) -> None:
        await self.__close_browser()

        portal_path = f'{os.path.dirname(os.path.abspath(__file__))}/temp/portal_{self.__id}.py'

        if self.__portal and os.path.exists(portal_path):
            os.remove(portal_path)


    @staticmethod
    def load_config(filename: str) -> Dict:
        with open(filename, 'r') as file:
            if get_file_type(filename) == 'yaml':
                return yaml.safe_load(file)
            elif get_file_type(filename) == 'json':
                return json.load(file)
                
        raise ValueError(Fore.RED + 'Unable to load unsupported config file type, ' + Fore.BLUE + filename + Fore.RESET)


    async def __start(self) -> None:
        self.__load_portal()
        await self.__launch_browser()

        if 'rake' not in self.__config: return self.data()

        self.__start_time = time.time()

        for page_config in self.__config['rake']:
            links = self.__resolve_page_link(page_config['link'])
            race = self.__config.get('race', 1)
            queue = asyncio.Queue(maxsize=race)
            tasks = [asyncio.create_task(self.__concurrent(queue, page_config)) for i in range(race)]

            for link in links:
                await queue.put(link)

            await queue.join()

            for _ in tasks:
                await queue.put(None)

            for ret in await asyncio.gather(*tasks, return_exceptions=True):
                if not isinstance(ret, Exception): continue
                raise ret


    async def __concurrent(self, queue: asyncio.Queue, config: PageConfig) -> None:
        while True:
            link: Link = await queue.get()

            if link is None: break

            page_manager = self.__PageManager(
                link,
                config,
                self.__config,
                self.__state,
                self.__browser_context,
                queue,
                self.__portal
            )
            
            try:
                await page_manager.open()
            except Exception as e:
                raise e
            finally:
                queue.task_done()

            self.__total_opened_pages += 1
    

    async def __launch_browser(self):
        playwright = await async_playwright().start()
        browser_config: Dict[str, Any] = self.__config.get('browser', {})
        browser_name: str = browser_config.get('type', 'chromium')

        if not hasattr(playwright, browser_name):
            raise ValueError(Fore.RED + 'Unsupported or invalid browser type, ' + Fore.CYAN + browser_name + Fore.RESET)
        
        kwargs = {}

        if 'show' in browser_config:
            kwargs['headless'] = not browser_config['show']
        
        if 'slowdown' in browser_config:
            kwargs['slow_mo'] = browser_config['slowdown']

        browser_type: BrowserType = getattr(playwright, browser_name)

        self.__browser = await browser_type.launch(**kwargs)
        self.__browser_context = await self.__browser.new_context()


    async def __close_browser(self) -> None:
        if not self.__browser.is_connected(): return
        if self.__config.get('logging', Rake.DEFAULT_LOGGING):
            print(Fore.YELLOW + 'Closing browser' + Fore.RESET)

        if self.__browser_context:
            self.__browser.is_connected
            await asyncio.gather(*[page.close() for page in self.__browser_context.pages])
            await self.__browser_context.close()
            await self.__browser.close()


    def __resolve_page_link(self, url: str | Dict | List[str | Dict]) -> List:
        urls: List[str | dict] = [url] if type(url) in [str, dict] else url
        links: List[Dict] = []

        for url in urls:
            if type(url) is dict:
                links.append(pick(url, {"url", "name", "metadata"}))
            elif url[0] == '$':
                links += self.__state['links'].get(url[1:], [])
            else:
                links.append({'url': url, 'name': url, 'metadata': {}})

        return links
    

    def __load_portal(self) -> None:
        if self.__config.get('portal', False) != True: return

        shutil.copy('portal.py', f'{os.path.dirname(os.path.abspath(__file__))}/temp/portal_{self.__id}.py')
        self.__portal = importlib.import_module(f'rake.temp.portal_{self.__id}')
    

    def __output(self, filepath: str, filetype: str, state: str = 'data', transform: str = None) -> None:
        if not filepath: return

        dir = os.path.dirname(filepath)
        data = self.__state[state]
        transform_fn: Callable | None = None
        transform_args: List[Dict | str] = [data, filepath]
        count_args: int = 0

        if dir: os.makedirs(dir, exist_ok=True)

        if transform:
            transform_fn, count_args = util.portal_action(transform, self.__config, self.__portal)
        
        match filetype:
            case 'yaml':
                if self.__config.get('logging', Rake.DEFAULT_LOGGING):
                    print(Fore.GREEN + f'Outputting {state} to YAML: ' + Fore.BLUE + filepath + Fore.RESET)

                if transform_fn:
                    data = transform_fn(*transform_args[0:count_args])

                # transform function should return None
                # when file creation is also handled
                if data is not None:
                    with open(filepath, 'w') as stream:
                        yaml.dump(data, stream)

            case 'json':
                if self.__config.get('logging', Rake.DEFAULT_LOGGING):
                    print(Fore.GREEN + f'Outputting {state} to JSON: ' + Fore.BLUE + filepath + Fore.RESET)

                if transform_fn:
                    data = transform_fn(*transform_args[0:count_args])

                if data is not None:
                    with open(filepath, 'w') as stream:
                        json.dump(data, stream, indent=2, ensure_ascii=False)

            case 'csv':
                if self.__config.get('logging', Rake.DEFAULT_LOGGING):
                    print(Fore.GREEN + f'Outputting {state} to CSV: ' + Fore.BLUE + filepath + Fore.RESET)

                if transform_fn and data:
                    data = transform_fn(*transform_args[0:count_args])
                
                if data is not None:
                    df = pd.DataFrame(data)
                    df.to_csv(filepath, index=False, header=False)

            case 'excel':
                if self.__config.get('logging', Rake.DEFAULT_LOGGING):
                    print(Fore.GREEN + f'Outputting {state} to Excel: ' + Fore.BLUE + filepath + Fore.RESET)

                if transform_fn and data:
                    data = transform_fn(*transform_args[0:count_args])

                if data is not None:
                    df = pd.DataFrame(data)
                    df.to_excel(filepath, index=False)

            case _:
                if transform_fn:
                    if self.__config.get('logging', Rake.DEFAULT_LOGGING):
                        print(Fore.GREEN + f'Outputting {state} to {filetype}: ' + Fore.BLUE + filepath + Fore.RESET)

                    transform_fn(*transform_args[0:count_args])


    def __get_outputs(self) ->  List[Dict[str, str]]:
        output_path: str = self.__config.get('output', {}).get('path', './')

        if not output_path.endswith('/'): output_path += '/'

        output_name: str = self.__config.get('output', {}).get('name', 'rake_output')
        formats: List[Dict | str] = self.__config.get('output', {}).get('formats', [])
        resolved_formats: List[Dict] = []
        format_file_extension = {
            'yaml': 'yml',
            'json': 'json',
            'excel': 'xlsx',
            'csv': 'csv'
        }

        for format in formats:
            format_config: Dict[str, str] = {}

            if type(format) is str:
                format_config['type'] = format
            else:
                format_config = format.copy()

            type_parts = format_config['type'].split(':')
            format_config['type'] = type_parts[0]
            file_extension = type_parts[1] if len(type_parts) > 1 else ''
            # to support empty file extension e.g. CSV:
            file_extension = file_extension if len(type_parts) > 1 else format_file_extension.get(format_config['type'].lower(), '')
            file_extension = f'.{file_extension}' if file_extension else ''
            format_config['path'] = f'{output_path}{output_name}{file_extension}'

            if format_config['type'].lower() in format_file_extension:
                format_config['type'] = format_config['type'].lower()
            
            resolved_formats.append(format_config)

        return resolved_formats


    class __PageManager:
        def __init__(
            self,
            link: Link,
            config: PageConfig,
            rake_config: Config,
            rake_state: State,
            browser_context: BrowserContext,
            queue: asyncio.Queue,
            portal: ModuleType | None = None
        ):
            self.__link = link
            self.__config = config
            self.__rake_config = rake_config
            self.__rake_state = rake_state
            self.__browser_context = browser_context
            self.__vars = link.get('metadata', {})
            self.__vars['_url'] = link['url']
            self.__page: Page | None = None
            self.__queue = queue
            self.__portal = portal

        async def open(self) -> Page:
            if 'interact' not in self.__config:
                return

            url = self.__link['url']

            if self.__rake_config.get('logging', Rake.DEFAULT_LOGGING):
                print(Fore.GREEN + Style.BRIGHT + 'Opening a new page: ' + Style.NORMAL + Fore.BLUE + url + Fore.RESET)

            page: Page = await self.__browser_context.new_page()
            self.__page = page
            browser_config: Dict[str, Any] = self.__rake_config.get('browser', {})
            viewport: List = browser_config.get('viewport', [])
            blacklisted_resources: List = browser_config.get('block', [])

            if len(viewport) == 2:
                await page.set_viewport_size({
                    'width': viewport[0],
                    'height': viewport[1]
                })

            if len(blacklisted_resources):
                await page.route(
                    '**/*',
                    lambda route: self.__block_request(route, blacklisted_resources)
                )

            kwargs = {}

            if 'ready_on' in browser_config:
                kwargs['wait_until'] = browser_config['ready_on']

            if 'timeout' in browser_config:
                kwargs['timeout'] = browser_config['timeout']
            
            await page.goto(url, **kwargs)
            await self.__interact(self.__config.get('interact'))
            await self.__close()

            return page


        async def __close(self) -> None:
            if not self.__page: return

            if self.__rake_config.get('logging', Rake.DEFAULT_LOGGING):
                print(Fore.YELLOW + 'Closing page: ' + Fore.BLUE + self.__page.url + Fore.RESET)

            await self.__page.close()


        async def __block_request(self, route: Route, types: List[str]) -> None:
            if route.request.resource_type in types:
                await route.abort()
            else:
                await route.continue_()
    

        async def __interact(self, interactions: InteractConfig) -> None:
            if 'repeat' in interactions:
                repeat = interactions['repeat']

                if type(repeat) is int:
                    for _ in range(repeat):
                        await self.__browse(interactions['nodes'])
                elif type(repeat) is list:
                    should_repeat = True

                    while True:
                        if not should_repeat: break

                        should_repeat = await self.__should_repeat(repeat)

                        await self.__browse(interactions['nodes'])

            else:
                await self.__browse(interactions['nodes'])


        async def __browse(self, nodes: List[NodeConfig]) -> None:
            for alts in nodes:
                alts = alts if type(alts) == list else [alts]

                for node in alts:
                    self.__vars['_node'] = re.sub(':', '-', node.get('name', node['element']))
                    loc_kwargs = {}

                    if 'contains' in node: loc_kwargs['has_text'] = node['contains']

                    if 'excludes' in node: loc_kwargs['has_not_text'] = node['excludes']

                    locator: Locator = self.__page.locator(node['element'], **loc_kwargs)

                    if self.__rake_config.get('logging', Rake.DEFAULT_LOGGING):
                        print(Fore.GREEN + 'Interacting with: ' + Fore.WHITE + Style.DIM + node['element'] + Style.NORMAL + Fore.RESET)

                    if 'wait' in node:
                        await locator.wait_for(timeout=node['wait'])

                    locs = await locator.all()
                    count = len(locs)

                    if not count: continue

                    all: bool = node.get('all', False)
                    rng_start, rng_stop, rng_step = self.__resolve_range(node.get('range', []), len(locs))
                    locs = locs[rng_start:rng_stop]
                    scroll_into_view = node.get('show', False)

                    if not all: locs = locs[0:1]

                    for i in range(0, len(locs), rng_step):
                        self.__vars['_nth'] = i
                        loc = locs[i]

                        if scroll_into_view and await loc.is_visible():
                            await loc.scroll_into_view_if_needed()

                        await self.__node_actions(node.get('actions', []), loc)

                        if 'links' in node:
                            await self.__add_links(loc, node['links'])

                        if 'data' in node:
                            await self.__extract_data(loc, node['data'], all)

                        if 'interact' in node:
                            await self.__interact(node['interact'])
                    
                    if count: break


        async def __should_repeat(self, conditions: List[Dict[str, Any]]) -> bool:
            for condition in conditions:
                value_getter = condition.get('value')
                repeat_while = condition.get('while')

                if not value_getter or not repeat_while or len(repeat_while) != 2: continue

                value = await self.__attribute(value_getter, self.__page.locator('html'))

                match repeat_while[0]:
                    case 'equal':
                        if value != repeat_while[1]: return False
                    case 'is':
                        if value != repeat_while[1]: return False
                    case 'not_equal':
                        if value == repeat_while[1]: return False
                    case 'not':
                        if value == repeat_while[1]: return False
                    case 'greater_than':
                        if value <= repeat_while[1]: return False
                    case 'less_than':
                        if value >= repeat_while[1]: return False
                    case 'greater_than_or_equal':
                        if value < repeat_while[1]: return False
                    case 'less_than_or_equal':
                        if value > repeat_while[1]: return False

            return True


        def __resolve_range(self, range: List, max: int) -> Tuple[int, int, int]:
            rng = dict(enumerate(range))
            rng_start: int = rng.get(0, 0)
            rng_start = 0 if rng_start == '_' else rng_start
            rng_stop: int = rng.get(1, max)
            rng_stop = max if rng_stop == '_' else rng_stop
            rng_step: int = rng.get(2, 1)
            rng_step = 1 if rng_step == '_' else rng_step

            return (rng_start, rng_stop, rng_step)


        async def __node_actions(self, actions: List[ActionConfig], loc: Locator) -> None:
            for action in actions:
                # pre-evaluate and cache screenshot file path,
                # before the node is removed or made inaccessible by action event
                screenshot_path = ''

                if 'screenshot' in action: 
                    screenshot_path = await self.__evaluate(action['screenshot'], loc)

                count = action.get('count', 1)

                if type(count) is str:
                    count = int(await self.__evaluate(count, loc))
                elif type(count) is dict:
                    count = int(await self.__attribute(count, loc))

                t: str = action['type']
                rect: DOMRect = await loc.evaluate("node => node.getBoundingClientRect()")

                for _ in range(count):
                    if 'delay' in action: 
                        await loc.page.wait_for_timeout(action['delay'])

                    if not await loc.is_visible() and self.__rake_config.get('logging', Rake.DEFAULT_LOGGING):
                        print(Fore.YELLOW + 'Action may fail due to node being inaccessible or not visible: ' + Fore.WHITE + f'{self.__vars['_node']}@{action['type']}')
                    
                    if action.get('dispatch', False) and t not in ['swipe_left', 'swipe_right']:
                        await loc.dispatch_event(action['type'])
                    elif t == 'click':
                        await loc.click(**pick(action.get('options', {}), {
                            'button': True,
                            'modifiers': True,
                        }))
                    elif t in ['swipe_left', 'swipe_right']:
                        if t == 'swipe_left':
                            start_x, end_x = (rect['x'] + rect['width']/2, 0)
                        else:
                            start_x, end_x = (rect['x'] + rect['width']/2, rect['x'] + rect['width'])
                            
                        start_y = end_y = rect['y'] + rect['height']/2
                        mouse = loc.page.mouse

                        await mouse.move(start_x, start_y)
                        await mouse.down()
                        await mouse.move(end_x, end_y)
                        await mouse.up()
                    else:
                        raise ValueError(Fore.RED + 'The ' + Fore.CYAN + t + Fore.RED + ' action is currently not supported' + Fore.RESET)
                            
                    if 'wait' in action:
                        await loc.page.wait_for_timeout(action['wait'])

                if 'screenshot' in action: 
                    await loc.page.screenshot(path=screenshot_path, full_page=True)


        async def __extract_data(self, loc: Locator, configs: List[DataConfig], all: bool = False) -> None:
            for config in configs:
                value = None

                if type(config['value']) is str:
                    value = await self.__evaluate(config['value'], loc)
                elif type(config['value']) is list:
                    value = await asyncio.gather(*[self.__evaluate(attr, loc) for attr in config['value']])
                elif type(config['value']) is dict:
                    value = {}

                    for key, attr in config['value'].items():
                        if type(attr) is str:
                            value[key] = await self.__evaluate(attr, loc)

                            continue

                        value[key] = await self.__attribute(attr, loc)

                value = [value] if all else value

                if type(value) is list and value[0] is None: value = []

                scope = keypath.resolve(
                    config['scope'],
                    self.__rake_state['data'],
                    self.__vars,
                    resolve_key=notation.find_item_key
                )

                if self.__rake_config.get('logging', Rake.DEFAULT_LOGGING):
                    print(Fore.GREEN + 'Extracting data to ' + Fore.CYAN + keypath.to_string(scope) + Fore.RESET)

                keypath.assign(value, self.__rake_state['data'], scope, merge=True)


        async def __add_links(self, loc: Locator, links: List[LinkConfig]) -> None:
            for link in links:
                name = link['name']
                smith = link.get('smith')
                metadata: Dict = {}
                result = await self.__evaluate(link['url'], loc)

                if name not in self.__rake_state['links']:
                    self.__rake_state['links'][name] = []

                if 'metadata' in link:
                    for key, value in link['metadata'].items():
                        if type(value) is str:
                            metadata[key] = await self.__evaluate(value, loc)
                        else:
                            metadata[key] = await self.__attribute(value, loc)

                if type(result) is not list:
                    result = [result]

                for url in result:
                    state_links: List[Link] = self.__rake_state['links'][name]
                    link_data = {'url': url, 'name': name, 'metadata': metadata}

                    if smith:
                        fn, args_count = util.portal_action(smith, self.__rake_config, self.__portal)
                        args = [url, name]
                        smithed_links = fn(*args[0:args_count])
                        
                        if type(smithed_links) is not list:
                            smithed_links = [smithed_links]

                        link_data = smithed_links

                    if type(link_data) is not list:
                        link_data = [link_data]

                    for link_item in link_data:
                        if type(link_item) is str:
                            link_item = {'url': link_item, 'name': name, 'metadata': metadata}
                        else:
                            link_item = util.pick(link_item, {'url', 'name', 'metadata'})

                        found_link = None

                        for existing_link in state_links:
                            if existing_link['url'] == link_item['url']:
                                found_link = existing_link
                                break

                        if found_link: continue

                        state_links.append(link_item)

                        if self.__link.get('name') == name:
                            await self.__queue.put(link_item)


        async def __evaluate(self, string: str, loc: Locator) -> str | List[str]:
            string_value = string
            getters = notation.parse_getters(string)

            for full_match, typ, var_name in getters:
                value = full_match

                match typ:
                    case 'attr':
                        value = await self.__attribute(var_name, loc)
                        if full_match == string: return value
                    case 'var':
                        value = str(self.__var(var_name, full_match))
                        if full_match == string: return value

                string_value = re.sub(re.escape(full_match), '' if value is None else str(value), string_value)

            return string_value


        async def __attribute(self, node_attr: Attribute, loc: Locator) -> str | List:
            values = []
            utils = {}
            locs = [loc]

            if type(node_attr) is str:
                result = notation.parse_value(node_attr)
                attr = result.get('prop')
                child_node = result.get('child_node')
                element = result.get('element')
                max = result.get('max')
                ctx = result.get('ctx')
                utils = result.get('parsed_utils')
                var_name = result.get('var')
            elif type(node_attr) is dict:
                attr = node_attr.get('attribute')
                child_node = node_attr.get('child_node')
                element = node_attr.get('element')
                max = node_attr.get('max', 'one')
                ctx = node_attr.get('context', 'parent')
                utils = node_attr.get('utils', {})
                var_name = node_attr.get('set_var')
            else:
                raise ValueError(Fore.RED + 'Invalid attribute type definition, only dict and str allowed at ' + Fore.WHITE + (element or self.__vars['_node']) + Fore.RESET)

            if not attr:
                raise ValueError(Fore.RED + 'Attribute to extract not define at ' + Fore.WHITE + (element or self.__vars['_node']) + Fore.RESET)

            if element:
                match ctx:
                    case 'parent':
                        locs = await loc.locator(element).all()
                    case 'page':
                        locs = await loc.page.locator(element).all()

            if attr == 'count': return int(self.__apply_utils(utils, len(locs)))

            if max == 'one': locs = locs[0:1]

            for loc in locs:
                value = None

                if attr in ['href', 'src', 'text']:
                    value = await loc.evaluate(
                        '(node, [childNode, attr]) => childNode ? node.childNodes[childNode - 1][attr] : node[attr]',
                        [child_node, 'textContent' if attr == 'text' else attr]
                    )
                elif attr == 'disabled':
                    value = await loc.is_disabled()

                if len(utils): 
                    value = self.__apply_utils(utils, value)

                values.append(value)

            if max == 'one': values: str = dict(enumerate(values)).get(0, '')

            if var_name: self.__vars[var_name] = values

            return values


        def __var(self, name: str, default: Any = None) -> Any:
            result = notation.parse_value(name, set_defaults=False)

            if not is_none_keys(result, 'child_node', 'ctx', 'max', 'element'):
                raise ValueError(Fore.RED + 'Invalid $var{...} notation at ' + Fore.CYAN + name + Fore.RESET)

            if result['prop'] in self.__vars:
                return self.__apply_utils(result['parsed_utils'], self.__vars[name])

            return default


        def __apply_utils(self, utils: Dict[str, List[str]], val: str):
            value = val

            for name, args in utils.items():
                match name.strip():
                    case 'prepend':
                        if len(args) > 0:
                            value = f'{args[0]}{value or ''}'
                    case 'lowercase':
                        value = str(value).lower()
                    case 'slug':
                        value = slugify(str(value))
                    case 'subtract':
                        if is_numeric(value): value = float(value)
                        else: value = 0.0

                        if len(args) > 0 and is_numeric(args[0]):
                            value = float(value) - float(args[0])
                    case 'clear_url_params':
                        value = value.split('?')[0]
                    case 'trim':
                        value = value.strip()
                    case 'nullify':
                        if not value: value = None
                    case _:
                        fn, _ = util.portal_action(name.strip(), self.__rake_config, self.__portal)
                        value = fn(value, *args)
            
            return value
        