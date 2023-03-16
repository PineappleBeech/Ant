import asyncio


class AtomicInteger:
    def __init__(self):
        self.value = 0
        self.lock = asyncio.Lock()

    async def get(self):
        async with self.lock:
            self.value += 1
            return self.value
