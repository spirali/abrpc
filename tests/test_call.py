import asyncio
import pytest
from abrpc import Connection, RemoteException, expose

def test_call(test_env, port):

    class MyService():

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



    service = MyService()

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