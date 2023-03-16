import inspect
import socket

from collections import defaultdict

from ant.util import AtomicInteger
from ant.reference import FunctionRef
import asyncio
from ant.network import Connection, HostPacketHandler

class Host:
    worker_funcs = defaultdict(dict)

    def __init__(self, port):
        self.port = port
        self.server = None
        self.workers = defaultdict(asyncio.Future)
        self.temp_workers = {}
        self.temp_workers_ids = AtomicInteger()

    def run(self):
        asyncio.create_task(self.run_async())

    async def run_async(self):
        self.server = await asyncio.start_server(self.handle_connection, "127.0.0.1", self.port)

    async def handle_connection(self, reader, writer):
        print("New connection")
        worker_id = await self.temp_workers_ids.get()
        self.temp_workers[worker_id] = Worker(self, worker_id, (reader, writer))


    async def get_worker(self, worker_id):
        return await self.workers[worker_id]


class Worker:
    def __init__(self, host, worker_id, pair):
        self._host = host
        self._worker_id = worker_id
        self._connection = Connection(pair, HostPacketHandler(self))
        self._funcs = {}
        self._funcs_scheduled = {}
        self._results = {}
        self._results_ids = AtomicInteger()
        asyncio.create_task(self._connection.run())

    def _register_id(self, id):
        old_id = self._worker_id
        self._worker_id = id
        self._host.workers[id].set_result(self)
        del self._host.temp_workers[old_id]

    async def _call(self, func_name, args):
        result_id = await self._results_ids.get()
        self._results[result_id] = asyncio.Future()
        if func_name in self._funcs_scheduled:
            await self._funcs_scheduled[func_name]
        await self._connection.send("call", (func_name, args, result_id))
        return await self._results[result_id]

    def _handle_result(self, data):
        result_id, result = data
        self._results[result_id].set_result(result)

    def __getattr__(self, item):
        if item in self._funcs:
            return FunctionRef(self, item)

        elif item in Host.worker_funcs[self._worker_id]:
            if item not in self._funcs_scheduled:
                self._send_function(item)
            self._funcs[item] = Host.worker_funcs[self._worker_id][item]
            return FunctionRef(self, item)

        raise AttributeError(f"No such function: {item}")

    def _send_function(self, func_name):
        func = Host.worker_funcs[self._worker_id][func_name]
        task = asyncio.create_task(self._connection.send("register_function", get_source(func)))
        self._funcs_scheduled[func_name] = task
        asyncio.create_task(self._send_function_cleanup(func_name))

    async def _send_function_cleanup(self, func_name):
        await self._funcs_scheduled[func_name]
        del self._funcs_scheduled[func_name]


def on_worker(worker_id):
    def decorator(func):
        Host.worker_funcs[worker_id][func.__name__] = func
        return func
    return decorator

def get_source(func):
    lines, _ = inspect.getsourcelines(func)
    return "".join([line for line in lines if not line.startswith("@")])