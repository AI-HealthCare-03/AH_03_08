import asyncio
from collections.abc import Generator
from typing import Any
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio
from _pytest.fixtures import FixtureRequest
from tortoise import generate_config
from tortoise.contrib.test import finalizer, initializer

from app.core import config
from app.core.db.databases import TORTOISE_APP_MODELS

TEST_BASE_URL = "http://test"
TEST_DB_LABEL = "models"
TEST_DB_TZ = "Asia/Seoul"


def get_test_db_config() -> dict[str, Any]:
    # .env ??DB_HOST=mysql(Docker) ????뚯뒪?몃뒗 localhost MySQL ?ъ슜 (CI쨌濡쒖뺄 docker compose)
    test_host = "mysql"
    tortoise_config = generate_config(
        db_url=f"mysql://{config.DB_USER}:{config.DB_PASSWORD}@{test_host}:{config.DB_PORT}/test",
        app_modules={TEST_DB_LABEL: TORTOISE_APP_MODELS},
        connection_label=TEST_DB_LABEL,
        testing=True,
    )
    tortoise_config["timezone"] = TEST_DB_TZ

    return tortoise_config


def _session_needs_db(request: FixtureRequest) -> bool:
    items = getattr(request.session, "items", [])
    if not items:
        return True
    return not all(item.get_closest_marker("no_db") is not None for item in items)


@pytest.fixture(scope="session", autouse=True)
def initialize(request: FixtureRequest) -> Generator[None, None]:
    if not _session_needs_db(request):
        yield
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with patch("tortoise.contrib.test.getDBConfig", Mock(return_value=get_test_db_config())):
        initializer(modules=TORTOISE_APP_MODELS)
    yield
    finalizer()
    loop.close()


@pytest_asyncio.fixture(autouse=True, scope="session")  # type: ignore[type-var]
def event_loop() -> None:
    pass
