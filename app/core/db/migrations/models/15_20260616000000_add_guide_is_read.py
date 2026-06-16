# aerich old-format 이슈로 자동 적용 불가 — DB에 직접 실행 필요
from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `guides` ADD `is_read` BOOL NOT NULL DEFAULT 0;
        ALTER TABLE `guides` ADD `read_at` DATETIME(6) NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `guides` DROP COLUMN `is_read`;
        ALTER TABLE `guides` DROP COLUMN `read_at`;"""
