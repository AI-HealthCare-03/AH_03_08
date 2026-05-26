from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `guides` ADD `title` VARCHAR(200);
        ALTER TABLE `feedbacks` ADD `tag_ids` JSON NOT NULL DEFAULT (JSON_ARRAY());"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `guides` DROP COLUMN `title`;
        ALTER TABLE `feedbacks` DROP COLUMN `tag_ids`;"""
