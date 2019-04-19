import sys
import os
import pytest
import asyncio

TEST_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(TEST_DIR)

sys.path.insert(0, ROOT_DIR)

from abrpc import on_connection  # noqa


@pytest.fixture()
def port():
    return 7321


@pytest.fixture()
def test_env(port):
    class TestEnv:

        def __init__(self):
            self.server = None

        def start_server(self, handle):
            srv = asyncio.start_server(on_connection(handle), port=port, reuse_port=True)
            self.server = self.run(srv)

        def run(self, coro):
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(coro)

    try:
        env = TestEnv()
        yield env
    finally:
        if env.server:
            env.server.close()
            loop = asyncio.get_event_loop()
            loop.run_until_complete(env.server.wait_closed())
            env.server = None
