import asyncio
from asyncio import IncompleteReadError
import msgpack
import traceback


class RemoteException(Exception):
    pass


class Connection:

    MESSAGE_CALL = 0
    MESSAGE_RESPONSE = 1

    def __init__(self, rw_pair):
        reader, writer = rw_pair
        self.reader = reader
        self.writer = writer
        self.service_running = False

        self.id_counter = 0
        self.running_calls = {}

    async def close(self):
        self.writer.close()
        # TODO: in 3.7
        #await self.writer.wait_closed()

    async def call(self, method_name, *args):
        assert isinstance(method_name, str)
        self.id_counter += 1
        message = [
            self.MESSAGE_CALL,
            self.id_counter,
            method_name,
            args
        ]
        future = asyncio.Future()
        self.running_calls[self.id_counter] = future
        await self._send_message(message)
        return await future

    async def serve(self, service=None):
        assert not self.service_running
        self.service_running = True

        while True:
            message = await self._read_message()
            if message is None:
                return
            if len(message) != 4:
                    raise Exception("Invalid message (Invalid wrapper)")
            # CALL
            if message[0] == self.MESSAGE_CALL:
                    asyncio.ensure_future(
                        self._run_method(service,
                                         message[1],
                                         message[2],
                                         message[3]))

            # RESPOSE
            elif message[0] == self.MESSAGE_RESPONSE:
                future = self.running_calls.pop(message[1])
                if message[2]:
                    future.set_result(message[3])
                else:
                    future.set_exception(RemoteException(str(message[3])))
                future = None
            else:
                raise Exception("Invalid message (Invalid message type)")
            message = None  # Do not hold reference to message while waiting for new message

    async def _read_message(self):
        try:
            size = await self.reader.readexactly(4)
        except IncompleteReadError as e:
            if not e.partial:
                return None
            raise e
        if not size:
            return None
        size = int.from_bytes(size, "big")
        return msgpack.unpackb(await self.reader.readexactly(size), raw=False)

    async def _send_error(self, call_id, error_message):
        self._send_message([
            self.MESSAGE_RESPONSE,
            call_id,
            False,
            error_message
        ])

    async def _run_method(self, service, call_id, method_name, args):
        method = getattr(service, method_name, None)
        if method is None or not getattr(method, "_abrpc_exposed", False):
            await self._send_error(call_id, "Method '{}' does not exist".format(method_name))
            return
        try:
            result = await method(*args)
            await self._send_message([
                self.MESSAGE_RESPONSE,
                call_id,
                True,
                result
            ])
        except:
            await self._send_error(call_id, traceback.format_exc())
            return

    def _send_message(self, message):
        data = msgpack.packb(message, use_bin_type=True)
        self.writer.write(len(data).to_bytes(4, "big"))
        self.writer.write(data)
        return self.writer.drain()