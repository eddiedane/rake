import asyncio, click
from rake import Rake

@click.command()
@click.argument('config_file', type=click.Path(exists=True))
def main(config_file):
    asyncio.run(rakestart(config_file))


async def rakestart(config_file: str):
    rake = Rake(Rake.load_config(config_file))
    error, _ = await rake.start()

    if error:
        raise error
    

if __name__ == '__main__':
    main()
