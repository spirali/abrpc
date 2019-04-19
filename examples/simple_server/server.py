
import asyncio
from abrpc import expose, on_connection

import uvloop     # Optional; for better performance
uvloop.install()


class ServerService():

    @expose()
    async def sum(self, x, y):
        return x + y


async def handle(conn):
    """ Handle incoming connection """
    print("New connection")
    await conn.serve(ServerService())
    print("Connection closed")

loop = asyncio.get_event_loop()
loop.run_until_complete(
    asyncio.start_server(on_connection(handle), port=8500))
loop.run_forever()
