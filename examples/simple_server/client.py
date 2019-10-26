import asyncio

from abrpc import Connection


async def main():
    conn = Connection(await asyncio.open_connection("localhost", port=8500))

    # Setup infrastructure
    conn.start_service()

    # Call remote service
    result = await conn.call("sum", 3, 2)
    print("Result =", result)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
