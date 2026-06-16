import asyncio
from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from _pytest.fixtures import FixtureRequest
from tortoise import generate_config
from tortoise.contrib.test import finalizer, initializer

from app.core import config
from app.core.db.databases import TORTOISE_APP_MODELS


def _make_mock_redis() -> AsyncMock:
    mock = AsyncMock()
    mock.exists.return_value = 0
    mock.incr.return_value = 1
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)

    async def mock_get(key: str) -> str | None:
        if key.startswith("email_token:"):
            return key.replace("email_token:", "")
        return None

    mock.get = AsyncMock(side_effect=mock_get)
    return mock


TEST_BASE_URL = "http://test"
TEST_DB_LABEL = "models"
TEST_DB_TZ = "Asia/Seoul"


def get_test_db_config() -> dict[str, Any]:
    # .env 의 DB_HOST=mysql(Docker) 대신 테스트는 localhost MySQL 사용 (CI·로컬 docker compose)
    test_host = "127.0.0.1"
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

    from app.main import app as fastapi_app

    fastapi_app.state.redis = _make_mock_redis()

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
