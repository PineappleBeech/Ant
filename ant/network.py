import abc
import asyncio
import struct
from ant.serializer import read_packet, write_packet


class Connection:
    def __init__(self, pair, packet_handler):
        self.reader, self.writer = pair
        self.packet_handler = packet_handler

    async def run(self):
        try:
            while True:
                size = await self.reader.readexactly(4)

                if not size:
                    break

                size = struct.unpack(">i", size)[0]
                data = await self.reader.readexactly(size)

                if not data:
                    break

                asyncio.create_task(self.packet_handler.handle(read_packet(data, skipsize=True)))

        except asyncio.IncompleteReadError:
            await self.close()
            print("Connection closed")

    async def send(self, name, data):
        print("Sending %s" % name)
        self.writer.write(write_packet(name, data))
        await self.writer.drain()

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()


class PacketHandler:
    def __init__(self):
        raise NotImplementedError()

    async def handle(self, packet):
        raise NotImplementedError()


class WorkerPacketHandler(PacketHandler):
    def __init__(self, worker):
        self.worker = worker

    async def handle(self, packet):
        name, data = packet
        print(f"Received {name}")

        if name == "register_function":
            self.register_function(data)

        elif name == "call":
            self.call(data)

        else:
            raise Exception(f"Unknown packet {name}")

    def register_function(self, data):
        self.worker.register_function(data)

    def call(self, data):
        self.worker.call(data)


# Host side but one per worker
class HostPacketHandler(PacketHandler):
    def __init__(self, worker):
        self.worker = worker

    async def handle(self, packet):
        name, data = packet
        print(f"Received {name}")

        if name == "result":
            self.handle_result(data)

        elif name == "register_id":
            self.register_id(data)

        else:
            raise Exception(f"Unknown packet {name}")

    def handle_result(self, data):
        self.worker._handle_result(data)

    def register_id(self, data):
        self.worker._register_id(data)
