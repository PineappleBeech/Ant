import asyncio
import time

from ant.host import Host, on_worker


@on_worker("test")
def five():
    print("five")
    return 5


async def main():
    host = Host()
    await host.run_async()

    worker = await host.get_worker("test")

    print(await worker.five())

if __name__ == '__main__':
    asyncio.run(main())
