import asyncio
import traceback

from ant.network import Connection, WorkerPacketHandler
from ant.serializer import write_packet, read_packet
from ant.consts import MULTICAST_GROUP, MULTICAST_PORT, PORT
import socket


class Worker:
    def __init__(self, id):
        self.id = id
        self.host = None
        self.port = PORT
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
        try:
            result = self.globals[func_name](*args)
        except Exception as e:
            trace = traceback.format_exc()
            asyncio.create_task(self.connection.send("exception", (result_id, trace)))
        else:
            asyncio.create_task(self.connection.send("result", (result_id, result)))

    def reset(self):
        self.globals = {}
        self.connection = None

    async def try_connect(self):
        if self.host is None:
            host = await self.try_get_host()
            print("Host:", host)

            if host is not None:
                self.host = host
            else:
                await asyncio.sleep(1)
                return

        try:
            pair = await asyncio.open_connection(self.host, self.port)
        except (ConnectionRefusedError, ConnectionAbortedError, OSError):
            await asyncio.sleep(1)
        else:
            self.connection = Connection(pair, WorkerPacketHandler(self))

    async def try_get_host(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
        s.sendto(write_packet("discover", 0), (MULTICAST_GROUP, MULTICAST_PORT))
        s.settimeout(1)
        try:
            data, addr = s.recvfrom(1024)
        except socket.timeout:
            pass
        else:
            name, data = read_packet(data)
            return data[1]

        return None

