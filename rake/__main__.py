import asyncio, click
from rake import Rake
from playwright._impl._errors import TargetClosedError
from colorama import Fore


@click.command()
@click.argument('config_file', type=click.Path(exists=True))
def main(config_file):
    asyncio.run(rakestart(config_file))


async def rakestart(config_file: str):
    rake = Rake(Rake.load_config(config_file))

    try:
        await rake.start()
    except TargetClosedError as e:
        print(Fore.RED + 'Browser closed unexpectedly' + Fore.LIGHTBLACK_EX + ' (10)' + Fore.RESET)
    except Exception as e:
        print(e, '(20)')
    finally:
        try:
            rake.data(output=True)
            await rake.end()
        except ValueError as e:
            print(e, '(30)')


if __name__ == '__main__':
    main()
