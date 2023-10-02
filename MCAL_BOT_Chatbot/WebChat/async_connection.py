import asyncio
from abc import ABC, abstractmethod
from collections import deque
from contextlib import asynccontextmanager

class ResourcePool(ABC):
    def __init__(self, max_resources):
        if max_resources < 1:
            raise ValueError(f'Invalid max_resources argument: {max_resources}')
        self._max_resources = max_resources
        self._request_lock = asyncio.Lock()
        self._resource_returned = asyncio.Condition()
        self._pool = deque()
        self._n_resources_created = 0
        self._is_hashable_resource = self.is_hashable_resource()
        self._in_use = set()

    async def close(self):
        """Close all resources."""

        async with self._request_lock:
            while self._pool:
                res = self._pool.popleft()
                await self.close_resource(res)
            while self._in_use:
                res = self._in_use.pop()
                await self.close_resource(res)

    async def close_resource(self, res):
        """Subclasses should override this method if the resource does
not implement a close method."""
        await res.close()

    def is_hashable_resource(self):
        """Override this function and return False if the resource cannot be
added to a set. Otherwise, we can do some additional error checking and
ensure that all resources are closed when method close is called."""
        return True

    @abstractmethod
    async def create_resource(self):
        pass

    async def get_resource(self, timeout=None):
        if timeout is None:
            timeout = 10

        while True:
            async with self._request_lock:
                if self._pool:
                    res = self._pool.popleft()
                    if self._is_hashable_resource:
                        self._in_use.add(res)
                    return res

                # Can we create another resource?
                if self._n_resources_created < self._max_resources:
                    self._n_resources_created += 1
                    res = await self.create_resource()
                    if self._is_hashable_resource:
                        self._in_use.add(res)
                    return res

                # We must wait for a resource to be returned
                async def wait_for_resource():
                    async with self._resource_returned:
                        await self._resource_returned.wait()

                try:
                    await asyncio.wait_for(wait_for_resource(), timeout=timeout)
                    # The pool now has at least one resource available and
                    # we will succeed on next iteration.
                except asyncio.TimeoutError:
                    raise RuntimeError("Timeout: No available resource in the pool.")


    async def release_resource(self, res):
        if self._is_hashable_resource:
            if res not in self._in_use:
                raise Exception('Releasing unknown object')
            # Could raise exception if two threads are releasing the same resource:
            self._in_use.remove(res)
        self._pool.append(res)
        # If someone is waiting for a resource:
        async with self._resource_returned:
            self._resource_returned.notify()

    @asynccontextmanager
    async def resource(self, timeout=None):
        res = await self.get_resource(timeout)
        try:
            yield res
        finally:
            await self.release_resource(res)


import aiosqlite3

class ConnectionPool(ResourcePool):
    def __init__(self, max_connections, database):
        super().__init__(max_connections)
        self._database = database

    async def create_resource(self):
        return await aiosqlite3.connect(self._database, asyncio.get_running_loop())

    def get_connection(self, timeout=None):
        return self.get_resource(timeout)

    def release_connection(self, connection):
        return self.release_resource(connection)

    def connection(self, timeout=None):
        return self.resource(timeout)


if __name__ == "__main__":
    async def worker(pool, n):
        try:
            for i in range(10):
                async with pool.connection() as conn:
                    cursor = await conn.cursor()
                    await cursor.execute('SELECT COUNT(*) FROM braintree_transaction')
                    row = await cursor.fetchone()
                    await cursor.close()
                    print(n, i, row[0])
                    await asyncio.sleep(.0001)
        except Exception as e:
            print(e)

    connection_pool = ConnectionPool(2, database='fncpl.db')
    tasks = [worker(connection_pool, n) for n in range(3)]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.run_until_complete(connection_pool.close())
    loop.close()