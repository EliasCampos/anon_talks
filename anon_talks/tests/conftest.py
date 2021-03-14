import asyncio

import pytest
from pypika.queries import Query
from tortoise import Tortoise

from anon_talks import _sync_db


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session', autouse=True)
def initialize_tests(event_loop):
    event_loop.run_until_complete(_sync_db(db_url="sqlite://:memory:"))
    yield
    event_loop.run_until_complete(Tortoise.close_connections())


@pytest.fixture(scope='function', autouse=True)
async def cleanup_db_tables():
    yield

    coros = [
        model._meta.db.execute_script(
            str(Query.from_(model._meta.db_table).delete())
        )
        for app in Tortoise.apps.values()
        for model in app.values()
    ]
    await asyncio.gather(*coros)
