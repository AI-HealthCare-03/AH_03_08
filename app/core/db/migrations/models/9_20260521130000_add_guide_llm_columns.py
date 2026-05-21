from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `guides` ADD `llm_model` VARCHAR(100);
        ALTER TABLE `guides` ADD `llm_temperature` DOUBLE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `guides` DROP COLUMN `llm_model`;
        ALTER TABLE `guides` DROP COLUMN `llm_temperature`;"""
