import asyncio, click
from rake import Rake
from playwright._impl._errors import TargetClosedError


@click.command()
@click.argument('config_file', type=click.Path(exists=True))
def main(config_file):
    asyncio.run(rakestart(config_file))


async def rakestart(config_file: str):
    rake = Rake(Rake.load_config(config_file))

    try:
        await rake.start()
    except TargetClosedError:
        rake.data()
        pass
    

if __name__ == '__main__':
    main()
