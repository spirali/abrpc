import asyncio
import pytest
from abrpc import Connection, RemoteException, expose


class MyCounterService():

    def __init__(self):
        self.counter = 0
        self.private_called = False

    @expose()
    async def increment(self, x):
        self.counter += x

    @expose()
    async def read(self):
        return self.counter

    async def not_public(self):
        self.private_called = True

    @expose()
    async def invalid(self):
        raise Exception("MyException")


def test_call(test_env, port):

    service = MyCounterService()

    async def handle(conn):
        await conn.serve(service)

    test_env.start_server(handle)

    async def main():
        conn = Connection(await asyncio.open_connection("localhost", port))
        asyncio.ensure_future(conn.serve())
        x = await conn.call("increment", 10)
        assert x is None
        x = await conn.call("read")
        assert x is 10
        x = await conn.call("increment", 6)
        assert x is None
        x = await conn.call("read")
        assert x is 16

        with pytest.raises(RemoteException) as einfo:
            await conn.call("xxx")

        assert "xxx" in str(einfo.value)
        assert "not exist" in str(einfo.value)

        with pytest.raises(RemoteException) as einfo:
            await conn.call("not_public")

        assert "not_public" in str(einfo.value)
        assert "not exist" in str(einfo.value)

        with pytest.raises(RemoteException) as einfo:
            await conn.call("invalid")

        assert "MyException" in str(einfo.value)

        await conn.close()

    test_env.run(main())
    assert service.counter == 16
    assert not service.private_called


def test_two_services(test_env, port):

    class ServerService:

        @expose()
        async def server_method(self):
            return "data"


    class ClientService:

        @expose()
        async def client_method(self, x, y):
            return x + y


    oneshot = asyncio.Future()

    async def handle(conn):
        f = asyncio.ensure_future(conn.serve(ServerService()))
        x = await conn.call("client_method", 10, 25)
        assert x == 35
        oneshot.set_result(None)
        await f

    test_env.start_server(handle)

    async def main():
        conn = Connection(await asyncio.open_connection("localhost", port))
        asyncio.ensure_future(conn.serve(ClientService()))
        x = await conn.call("server_method")
        assert x == "data"
        await oneshot

    test_env.run(main())



def test_call_no_response(test_env, port):

    service = MyCounterService()

    async def handle(conn):
        await conn.serve(service)

    test_env.start_server(handle)

    error_msg = [None]

    def error_callback(call_id, msg):
        assert "xxx" in msg
        error_msg[0] = msg

    async def main():

        conn = Connection(await asyncio.open_connection("localhost", port))
        conn.set_on_error_no_response_call(error_callback)
        asyncio.ensure_future(conn.serve())
        x = await conn.call_no_response("increment", 10)
        assert x is None
        x = await conn.call_no_response("increment", 10)
        assert x is None
        x = await conn.call_no_response("read")
        assert x is None

        assert error_msg[0] is None
        x = await conn.call_no_response("xxx", 10)
        x = await conn.call("read")
        assert error_msg[0]
        assert x == 20

    test_env.run(main())

    assert service.counter == 20
