from typing import Dict, Any
import asyncio
from colorama import Fore
from playwright.async_api import async_playwright, Browser, BrowserContext, BrowserType


class Rake:
  __browser_context: BrowserContext = None
  __browser: Browser = None
  __config: Dict[str, Any] = {}

  def __init__(self, config: Dict[str, Any]):
    self.__config = config
    self.__state = {'data': {}, 'vars': {}, 'links': {}}

  async def go(self):
    try:
      await self.__start()
    except Exception as e:
      raise e
    finally:
      await self.__close_browser()
        

  async def __start(self):

    if 'rake' not in self.__config: return

    await self.__launch_browser()

    page = await self.__browser_context.new_page()
    await page.goto('https://google.com')

    print('do raking')

  async def __launch_browser(self):
    playwright = await async_playwright().start()
    browser_config = self.__config.get('browser', {})
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

    await asyncio.gather(*[page.close() for page in self.__browser_context.pages])

    await self.__browser_context.close()
    await self.__browser.close()

