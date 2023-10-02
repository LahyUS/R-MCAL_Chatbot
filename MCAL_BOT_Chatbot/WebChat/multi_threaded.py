from abc import ABC, abstractmethod
from collections import deque
from threading import Lock, Condition
from contextlib import contextmanager

class ResourcePool(ABC):
    def __init__(self, max_resources):
        if max_resources < 1:
            raise ValueError(f'Invalid max_resources argument: {max_resources}')
        self._max_resources = max_resources
        self._request_lock = Lock()
        self._resource_returned = Condition()
        self._pool = deque()
        self._n_resources_created = 0
        self._is_hashable_resource = self.is_hashable_resource()
        self._in_use = set()

    def close(self):
        """Close all resources."""

        with self._request_lock:
            while self._pool:
                self.close_resource(self._pool.popleft())
            while self._in_use:
                self.close_resource(self._in_use.pop())

    def close_resource(self, res):
        """Subclasses should override this method if the resource does
not implement a close method."""
        res.close()

    def __del__(self):
        """Close all resources when the pool is garbage
collected. Note that due to how close is implemented, it may be
called multiple times."""
        self.close()

    def is_hashable_resource(self):
        """Override this function and return False if the resource cannot be
added to a set. Otherwise, we can do some additional error checking and
ensure that all resources are closed when method close is called."""
        return True

    @abstractmethod
    def create_resource(self):
        pass

    def get_resource(self, timeout=None):
        if timeout is None:
            timeout = 10

        with self._request_lock:
            while True:
                if self._pool:
                    res = self._pool.popleft()
                    if self._is_hashable_resource:
                        self._in_use.add(res)
                    return res

                # Can we create another resource?
                if self._n_resources_created < self._max_resources:
                    self._n_resources_created += 1
                    res = self.create_resource()
                    if self._is_hashable_resource:
                        self._in_use.add(res)
                    return res

                # We must wait for a resource to be returned
                with self._resource_returned:
                    if not self._resource_returned.wait(timeout=timeout):
                        raise RuntimeError("Timeout: No available resource in the pool.")
                    # The pool now has at least one resource available and
                    # we will succeed on next iteration.

    def release_resource(self, res):
        if self._is_hashable_resource:
            if res not in self._in_use:
                raise Exception('Releasing unknown object')
            # Could raise exception if two threads are releasing the same resource:
            self._in_use.remove(res)
        self._pool.append(res)
        # Notify the thread waiting for a resource, if any:
        with self._resource_returned:
            self._resource_returned.notify()

    @contextmanager
    def resource(self, timeout=None):
        res = self.get_resource(timeout)
        try:
            yield res
        finally:
            self.release_resource(res)


import mysql.connector

class ConnectionPool(ResourcePool):
    def __init__(self, max_connections, database, user, password, time_zone='America/New_York'):
        super().__init__(max_connections)
        self._database = database
        self._user = user
        self._password = password
        self._time_zone = time_zone

    def create_resource(self):
        return mysql.connector.connect(database=self._database,
                                       user=self._user,
                                       password=self._password,
                                       charset='utf8mb4',
                                       use_unicode=True,
                                       init_command=f"set session time_zone='{self._time_zone}'"
                                       )

    def get_connection(self, timeout=None):
        return self.get_resource(timeout)

    def release_connection(self, connection):
        return self.release_resource(connection)

    def connection(self, timeout=None):
        return self.resource(timeout)

if __name__ == '__main__':
    from multiprocessing.pool import ThreadPool

    def worker(pool, n):
        try:
            for i in range(10):
                with pool.connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM transaction')
                    cnt = cursor.fetchone()[0]
                    cursor.close()
                    print(n, i, cnt)
        except Exception as e:
            print(e)

    connection_pool = ConnectionPool(2, database='test_db', user='***', password='***')
    thread_pool = ThreadPool(3)
    for n in range(3):
        thread_pool.apply_async(worker, args=(connection_pool, n))
    thread_pool.close()
    thread_pool.join()