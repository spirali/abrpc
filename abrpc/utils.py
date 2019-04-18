from .connection import Connection

def on_connection(callback):
    async def helper(reader, writer):
        try:
            connection = Connection((reader, writer))
            await callback(connection)
        finally:
            await connection.close()
    return helper


def _expose_helper(fn):
    fn._abrpc_exposed = True
    return fn

def expose():
    return _expose_helper