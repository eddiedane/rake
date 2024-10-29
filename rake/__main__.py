import asyncio, os, click
from os import path

from click import Context
from rake import Rake
from playwright._impl._errors import TargetClosedError
from colorama import Fore


@click.group(invoke_without_command=True)
@click.argument('config_file', required=False, type=click.Path(exists=True))
@click.option('--cleanup', is_flag=True, help='Cleanup temporary/stale files')
@click.pass_context
def main(ctx: Context, config_file: str, cleanup: bool):
    if cleanup:
        cleanup_files()

    if config_file:
        asyncio.run(rakestart(config_file))

    if not cleanup and not config_file:
        click.echo(ctx.get_help())


async def rakestart(config_file: str):
    rake = Rake(Rake.load_config(config_file))

    try:
        await rake.start()
    except TargetClosedError as e:
        print(Fore.RED + 'Browser closed unexpectedly' + Fore.LIGHTBLACK_EX + Fore.RESET)
    except KeyError as e:
        print(Fore.RED + 'Invalid configuration, missing key:' + Fore.LIGHTBLACK_EX + f' {e}' + Fore.RESET)
    except Exception as e:
        print(e)
    finally:
        try:
            await rake.end()
            rake.data(output=True)
        except ValueError as e:
            print(e)


def cleanup_files():
    temp_dir = path.join(path.dirname(path.abspath(__file__)), 'temp')
    portal_files_count = 0

    for file in os.listdir(temp_dir):
        if file.startswith('portal_'):
            portal_files_count += 1
            os.remove(path.join(temp_dir, file))

    if portal_files_count == 0:
        click.echo(Fore.BLACK + 'Already neat and tidy' + Fore.RESET)
    else:
        click.echo(Fore.GREEN + f'Cleaned up {portal_files_count} stale file' + ('' if portal_files_count == 1 else 's') + Fore.RESET)


if __name__ == '__main__':
    main()
