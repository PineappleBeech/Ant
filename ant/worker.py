import asyncio
from ant.network import Connection, WorkerPacketHandler

class Worker:
    def __init__(self, id, host, port):
        self.id = id
        self.host = host
        self.port = port
        self.globals = {}
        self.connection = None

    def run(self):
        asyncio.run(self.run_async())

    async def run_async(self):
        while True:
            while self.connection is None:
                await self.try_connect()

            await self.connection.send("register_id", self.id)
            await asyncio.create_task(self.connection.run())
            self.reset()

    def register_function(self, func):
        exec(func, self.globals)

    def call(self, data):
        func_name, args, result_id = data
        result = self.globals[func_name](*args)
        asyncio.create_task(self.connection.send("result", (result_id, result)))

    def reset(self):
        self.globals = {}
        self.connection = None

    async def try_connect(self):
        try:
            pair = await asyncio.open_connection(self.host, self.port)
        except ConnectionRefusedError:
            await asyncio.sleep(1)
        else:
            self.connection = Connection(pair, WorkerPacketHandler(self))
