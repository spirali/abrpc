import asyncio

from abrpc import on_connection, Connection


def test_multiple_connect_close(port):

    connections = [0]
    async def handle_conn(conn):
        connections[0] += 1
        await conn.close()

    async def main():
        await asyncio.start_server(on_connection(handle_conn), port=port, reuse_port=True)
        r, _ = await asyncio.open_connection("localhost", port)
        assert await r.read() == b""
        r, _ = await asyncio.open_connection("localhost", port)
        assert await r.read() == b""
        r, _ = await asyncio.open_connection("localhost", port)
        assert await r.read() == b""

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

    assert connections[0] == 3