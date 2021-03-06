from .connection import Connection


def on_connection(callback):
    async def helper(reader, writer):
        connection = Connection((reader, writer))
        await callback(connection)

    return helper


def _expose_helper(fn):
    fn._abrpc_exposed = True
    return fn


def expose():
    return _expose_helper
