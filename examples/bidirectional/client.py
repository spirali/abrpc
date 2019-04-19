import asyncio
from abrpc import Connection, expose


class ClientService():

    @expose()
    async def get_name(self):
        return "ClientService!"

    @expose()
    async def get_x(self):
        return 123


async def main():
    conn = Connection(await asyncio.open_connection("localhost", port=8500))

    # Setup infrastructure
    asyncio.ensure_future(conn.serve(ClientService()))

    # Call remote service
    result = await conn.call("sum", 3, 2)
    print("Result =", result)

    # For simplicity, we sleep for some time, to give a chace a server call us
    await asyncio.sleep(1)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
