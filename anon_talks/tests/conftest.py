import asyncio
import os

import pytest
from pypika.queries import Query
from tortoise import Tortoise
from tortoise.contrib.test import finalizer, initializer, _restore_default


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session', autouse=True)
def initialize_tests(request):
    db_url = os.environ.get("TORTOISE_TEST_DB", "sqlite://:memory:")
    initializer(['anon_talks.models'], db_url=db_url, app_label='anon_talks')
    _restore_default()
    request.addfinalizer(finalizer)


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
