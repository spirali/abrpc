import os
import sys
import asyncio
import multiprocessing
import time
import uvloop

uvloop.install()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abrpc import Connection, on_connection, expose

def server_process():
    class ServerService():

        @expose()
        async def sum(self, x, y):
            return x + y

    async def handle(conn):
        await conn.serve(ServerService())

    f = asyncio.start_server(on_connection(handle), port=8500)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(f)
    loop.run_forever()


async def client_process():
    COUNT = 20000
    conn = Connection(await asyncio.open_connection("localhost", port=8500))
    asyncio.ensure_future(conn.serve())

    conn.set_nr_error_handle(lambda x, y: 0)

    start_time = time.time()
    for _ in range(COUNT):
        await conn.call("sum", 1, 2)
    end_time = time.time()
    duration = end_time - start_time
    print("call & wait: Calls/s: {}".format(COUNT/duration))

    start_time = time.time()
    for _ in range(COUNT):
        await conn.call_no_response("sum", 1, 2)
    end_time = time.time()
    duration = end_time - start_time
    print("call_no_response: Calls/s: {}".format(COUNT/duration))

    #start_time = time.time()
    #fs = []
    #for _ in range(COUNT):
    #    fs.append(conn.call("sum", 1, 2))
    #await asyncio.wait(fs)
    #end_time = time.time()
    #duration = end_time - start_time
    #print("call & wait_all: Calls/s: {}".format(COUNT/duration))

def main():
    p = multiprocessing.Process(target=server_process)
    p.start()
    time.sleep(1.0)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(client_process())
    p.terminate()


if __name__ == "__main__":
    main()
