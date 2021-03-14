import pytest
from aioresponses import aioresponses


@pytest.fixture
def aiohttp_client_mock():
    with aioresponses() as mock:
        yield mock
