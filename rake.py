import asyncio
import re, json, os, yaml, time
from typing import Dict, Any, List, Literal, Tuple
from colorama import Fore, Style
from slugify import slugify
from tabulate import tabulate
from playwright.async_api import async_playwright, Browser, BrowserContext, BrowserType, Page, Locator, Route
from utils.helpers import pick, is_none_keys, is_numeric, is_file_type, get_total_size
from utils import notation, keypath


Config = Dict[Literal['browser', 'rake'], Dict]

NodeConfig = Dict[Literal['selector', 'all', 'range', 'links', 'data', 'nodes', 'actions', 'wait', 'contains', 'excludes'], int | str | bool | List | Dict]

LinkConfig = Dict[Literal['name', 'url', 'metadata'], str | Dict[str, Any]]

DataConfig = Dict[Literal['scope', 'value'], str | List[str] | Dict[str, Any]]

ActionConfig = Dict[Literal['type', 'delay', 'wait', 'screenshot', 'dispatch', 'count'], str | int | bool]

Link = Dict[Literal['url', 'metadata'], str | Dict[str, Any]]

Links = Dict[str, List[Link]]

DOMRect = Dict[Literal['x', 'y', 'width', 'height', 'top', 'right', 'bottom', 'left'], float]


class Rake:

    def __init__(self, config: Dict[str, Any]):
        self.__browser_context: BrowserContext = None
        self.__browser: Browser = None
        self.__config = config
        self.__state = {'data': {}, 'vars': {}, 'links': {}}
        self.__start_time = 0
        self.__total_opened_pages = 0


    async def start(self):
        try:
            return (None, await self.__start())
        except Exception as e:
            return (e, None)
        finally:
            print(Fore.YELLOW + 'Finally' + Fore.RESET)
            await self.__close_browser()
            print()
            self.table()
            print()


    def data(self, filepath: str | None = None) -> Dict | None:
        if not filepath: return self.__state['data']

        self.__output(filepath)


    def links(self, filepath: str | None = None) -> Dict | None:
        if not filepath: return self.__state['links']

        self.__output(filepath, state='links')


    def table(self) -> None:
        duration = str(int(time.time() - self.__start_time)) + ' seconds'
        data_size = str(round(get_total_size(self.__state['data'])/1024, 2)) + ' KBs'
        mode = 'background' if not self.__config.get('browser', {}).get('show', False) else 'visible'
        output = 'dict'

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


    @staticmethod
    def load_config(filename: str) -> Dict:
        with open(filename, 'r') as file:
            if is_file_type('yaml', filename):
                return yaml.safe_load(file)
            elif is_file_type('json', filename):
                return json.load(file)
            
        raise ValueError(Fore.RED + 'Unable to load unsupported config file type, ' + Fore.BLUE + filename + Fore.RESET)


    async def __start(self):

        await self.__launch_browser()

        if 'rake' not in self.__config: return self.data()

        self.__start_time = time.time()

        for page_conf in self.__config['rake']:
            links = self.__resolve_page_link(page_conf['link'])
            
            for link in links:
                page = await self.__new_page(link['url'])
                self.__state['vars'] = link.get('metadata', {})
                self.__state['vars']['_url'] = page.url

                nodes = page_conf.get('nodes', [])

                if not len(nodes):
                    await self.__close_pages()
                    continue
                
                if 'repeat' in page_conf:
                    repeat = page_conf['repeat']

                    if type(repeat) is int:
                        for _ in range(repeat):
                            await self.__interact(page, nodes)
                    elif type(repeat) is dict:
                        while await self.__should_repeat(page, repeat):
                            await self.__interact(page, nodes)
                else:
                    await self.__interact(page, nodes)

                await self.__close_pages()

        return self.data()
    

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
        if self.__config.get('logging', False):
            print(Fore.YELLOW + 'Closing browser' + Fore.RESET)

        if self.__browser_context:
            await asyncio.gather(*[page.close() for page in self.__browser_context.pages])
            await self.__browser_context.close()
            await self.__browser.close()


    async def __new_page(self, url: str) -> Page:
        if self.__config.get('logging', False):
            print(Fore.GREEN + Style.BRIGHT + 'Opening a new page: ' + Style.NORMAL + Fore.BLUE + url + Fore.RESET)

        page: Page = await self.__browser_context.new_page()
        browser_config: Dict[str, Any] = self.__config.get('browser', {})
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

        self.__total_opened_pages += 1

        return page


    async def __close_pages(self, start: int = 1, end: int = None) -> None:
        page_slice: slice = slice(start, end, 1)

        if self.__config.get('logging', False):
            pages_url = [page.url for page in self.__browser_context.pages[page_slice]]

            print(Fore.YELLOW + 'Closing page: ' + Fore.BLUE + ', '.join(pages_url) + Fore.RESET)

        await asyncio.gather(*[page.close() for page in self.__browser_context.pages[page_slice]])


    async def __block_request(self, route: Route, types: List[str]) -> None:
        if route.request.resource_type in types:
            await route.abort()
        else:
            await route.continue_()
    

    async def __interact(self, page: Page, nodes: List[NodeConfig]) -> None:
        for alts in nodes:
            alts = alts if type(alts) == list else [alts]

            for node in alts:

                self.__state['vars']['_node'] = re.sub(':', '-', node.get('name', node['selector']))
                loc_kwargs = {}

                if 'contains' in node: loc_kwargs['has_text'] = node['contains']

                if 'excludes' in node: loc_kwargs['has_not_text'] = node['excludes']

                locator: Locator = page.locator(node['selector'], **loc_kwargs)

                if self.__config.get('logging', False):
                    print(Fore.GREEN + 'Interacting with: ' + Fore.WHITE + Style.DIM + node['selector'] + Style.NORMAL + Fore.RESET)

                if 'wait' in node:
                    try: await locator.wait_for(timeout=node['wait'])
                    except TimeoutError as e: raise e

                locs = await locator.all()
                count = len(locs)

                if not count: continue

                all: bool = node.get('all', False)
                rng_start, rng_stop, rng_step = self.__resolve_range(node.get('range', []), len(locs))
                locs = locs[rng_start:rng_stop]
                scroll_into_view = node.get('show', False)

                if not all: locs = locs[0:1]

                for i in range(0, len(locs), rng_step):
                    self.__state['vars']['_nth'] = i
                    loc = locs[i]

                    if scroll_into_view: await loc.scroll_into_view_if_needed()

                    await self.__node_actions(node.get('actions', []), loc)

                    if 'links' in node: await self.__add_links(loc, node['links'])

                    if 'data' in node: await self.__extract_data(loc, node['data'], all)

                    if 'nodes' in node: await self.__interact(page, node['nodes'])
                
                if count: break


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

            t: str = action['type']
            rect: DOMRect = await loc.evaluate("node => node.getBoundingClientRect()")

            for _ in range(count):
                if 'delay' in action: 
                    await loc.page.wait_for_timeout(action['delay'])

                if not await loc.is_visible() and self.__config.get('logging', False):
                    print(Fore.YELLOW + 'Action may fail due to node being inaccessible or not visible: ' + Fore.WHITE + f'{self.__state['vars']['_node']}@{action['type']}')
                
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


    async def __evaluate(self, string: str, loc: Locator) -> str | List[str]:
        list_string = []
        getters = notation.parse_getters(string)

        for full_match, typ, var_name in getters:
            value = full_match

            match typ:
                case 'attr': value = await self.__attribute(var_name, loc)
                case 'var': value = str(self.__var(var_name, full_match))

            if type(value) is not list:
                string = re.sub(re.escape(full_match), str(value), string)
            else:
                list_string += value

        return string if not len(list_string) else list_string
    

    async def __attribute(self, node_attr: str, loc: Locator) -> str | List:
        values = []
        utils = []
        locs = [loc]
        result = notation.parse_value(node_attr)
        attr = result['prop']
        child_node = result['child_node']
        selector = result['selector']
        max = result['max']
        ctx = result['ctx']
        utils = result['parsed_utils']
        var_name = result['var']

        if not attr : raise ValueError(Fore.RED + 'Attribute to extract not define at ' + Fore.WHITE + (selector or self.__state['vars']['_node']) + Fore.RESET)

        if selector:
            match ctx:
                case 'parent': locs = await loc.locator(selector).all()
                case 'page': locs = await loc.page.locator(selector).all()

        if attr == 'count': return int(self.__apply_utils(utils, len(locs)))

        if max == 'one': locs = locs[0:1]

        for loc in locs:
            value = None

            if attr in ['href', 'src', 'text']:
                value = await loc.evaluate(
                    '(node, [childNode, attr]) => childNode ? node.childNodes[childNode - 1][attr] : node[attr]',
                    [child_node, 'textContent' if attr == 'text' else attr]
                )

            if len(utils): 
                value = self.__apply_utils(utils, value)

            values.append(value)

        if max == 'one': values: str = dict(enumerate(values)).get(0, '')

        if var_name: self.__state['vars'][var_name] = values

        return values
    

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
                self.__state['data'],
                self.__state['vars'],
                resolve_key=notation.find_item_key
            )

            if self.__config.get('logging', False):
                print(Fore.GREEN + 'Extracting data to ' + Fore.CYAN + keypath.to_string(scope) + Fore.RESET)

            keypath.assign(value, self.__state['data'], scope, merge=True)


    async def __add_links(self, loc: Locator, links: List[LinkConfig]) -> None:
        for link in links:
            name = link['name']
            metadata: Dict = {}
            result = await self.__evaluate(link['url'], loc)

            if name not in self.__state['links']:
                self.__state['links'][name] = []

            if 'metadata' in link:
                for key, value in link['metadata'].items():
                    metadata[key] = await self.__evaluate(value, loc)

            if type(result) is not list:
                self.__state['links'][name].append({'url': result, 'metadata': metadata})
                continue
            
            for string in result:
                # type
                self.__state['links'][name].append({'url': string, 'metadata': metadata})


    def __var(self, name: str, default: Any = None) -> Any:
        result = notation.parse_value(name, set_defaults=False)

        if not is_none_keys(result, 'child_node', 'ctx', 'max', 'selector'):
            raise ValueError(Fore.RED + 'Invalid $var{...} notation at ' + Fore.CYAN + name + Fore.RESET)

        if result['prop'] in self.__state['vars']:
            return self.__apply_utils(result['parsed_utils'], self.__state['vars'][name])
        
        return default
    

    async def __should_repeat(self, page: Page, opts: Dict) -> bool:
        loc: Locator = page.locator(opts['selector'])
        loc = loc.first

        if 'exists' in opts and bool(await loc.count()) == opts['exists']: return True

        if 'disabled' in opts and await loc.is_disabled() == opts['disabled']: return True

        return False


    def __apply_utils(self, utils: List[Tuple[str, List]], val: str):
        value = val

        for name, args in utils:
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
        
        return value


    def __resolve_page_link(self, url: str | Dict | List[str | Dict]) -> List:
        urls: List[str | dict] = [url] if type(url) in [str, dict] else url
        links: List[Dict] = []

        for url in urls:
            if type(url) is dict:
                # exclude internally set keys e.g. parent
                links.append(pick(url, {"url", "metadata"}))
            elif url[0] == '$':
                links += self.__state['links'].get(url[1:], [])
            else:
                links.append({'url': url, 'metadata': {}})

        return links
    

    def __resolve_range(self, range: List, max: int) -> Tuple[int, int, int]:
        rng = dict(enumerate(range))
        rng_start: int = rng.get(0, 0)
        rng_start = 0 if rng_start == '_' else rng_start
        rng_stop: int = rng.get(1, max)
        rng_stop = max if rng_stop == '_' else rng_stop
        rng_step: int = rng.get(2, 1)
        rng_step = 1 if rng_step == '_' else rng_step

        return (rng_start, rng_stop, rng_step)
    

    def __output(self, filepath: str, state: str = 'data') -> None:
        if not filepath: return

        dir = os.path.dirname(filepath)
        data = self.__state[state]

        if dir: os.makedirs(dir, exist_ok=True)

        with open(filepath, 'w') as stream:

            if is_file_type('yaml', filepath):
                if self.__config.get('logging', False):
                    print(Fore.GREEN + f'Outputting {state} to YAML: ' + Fore.BLUE + filepath + Fore.RESET)

                yaml.dump(data, stream)

            if is_file_type('json', filepath):
                if self.__config.get('logging', False):
                    print(Fore.GREEN + f'Outputting {state} to JSON: ' + Fore.BLUE + filepath + Fore.RESET)

                json.dump(data, stream, indent=2, ensure_ascii=False)

