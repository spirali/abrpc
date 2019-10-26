import asyncio
import traceback
from asyncio import IncompleteReadError

import msgpack


class RemoteException(Exception):
    pass


class Connection:
    MESSAGE_CALL = 0
    MESSAGE_RESPONSE = 1
    MESSAGE_CALL_NO_RESPONSE = 2

    def __init__(self, rw_pair):
        reader, writer = rw_pair
        self.reader = reader
        self.writer = writer
        self.service_running = False

        self.id_counter = 0
        self.running_calls = {}
        self.nr_error_handle = None
        self.service_future = None

    def set_nr_error_handle(self, callback):
        self.nr_error_handle = callback

    async def close(self):
        self.writer.close()
        # TODO: in 3.7
        # await self.writer.wait_closed()

        if self.service_future:
            self.service_future.cancel()
            self.service_future = None

    async def call(self, method_name, *args):
        future = asyncio.Future()
        self.running_calls[self.id_counter] = future
        await self._send_call(method_name, args, False)
        return await future

    async def call_no_response(self, method_name, *args):
        if self.nr_error_handle is None:
            raise Exception(
                "No error handler set for no_response calls. "
                "Use set_on_error_resposen_call()")
        await self._send_call(method_name, args, True)

    def start_service(self, service=None):
        if self.service_future:
            raise Exception("Service future already running")
        self.service_future = asyncio.ensure_future(self.serve(service))

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
                    self._run_method(
                        service, message[1], message[2], message[3], False))
            # CALL_NO_RESPONSE
            elif message[0] == self.MESSAGE_CALL_NO_RESPONSE:
                asyncio.ensure_future(
                    self._run_method(
                        service, message[1], message[2], message[3], True))
            # RESPOSE
            elif message[0] == self.MESSAGE_RESPONSE:
                future = self.running_calls.pop(message[1], None)
                if message[2]:
                    future.set_result(message[3])
                else:
                    if future is None:
                        self.nr_error_handle(message[2], str(message[3]))
                    else:
                        future.set_exception(RemoteException(str(message[3])))
                    future = None
            else:
                raise Exception("Invalid message (Invalid message type)")

            # Do not hold reference to message while waiting for new message
            message = None

    def _send_call(self, method_name, args, no_response):
        assert isinstance(method_name, str)
        message = [
            self.MESSAGE_CALL_NO_RESPONSE if no_response else self.MESSAGE_CALL,
            self.id_counter,
            method_name,
            args
        ]
        self.id_counter += 1
        return self._send_message(message)

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

    def _send_error(self, call_id, error_message):
        return self._send_message([
            self.MESSAGE_RESPONSE,
            call_id,
            False,
            error_message
        ])

    async def _run_method(self, service, call_id, method_name, args, no_response):
        method = getattr(service, method_name, None)
        if method is None or not getattr(method, "_abrpc_exposed", False):
            if service is None:
                await self._send_error(call_id, "No service registered")
            else:
                await self._send_error(
                    call_id, "Method '{}' does not exist or is not exposed on '{}'".format(
                        method_name, type(service).__name__))
            return
        try:
            result = await method(*args)
            if no_response:
                return
            await self._send_message([
                self.MESSAGE_RESPONSE,
                call_id,
                True,
                result
            ])
        except Exception:
            await self._send_error(call_id, traceback.format_exc())

    def _send_message(self, message):
        data = msgpack.packb(message, use_bin_type=True)
        self.writer.write(len(data).to_bytes(4, "big"))
        self.writer.write(data)
        return self.writer.drain()
