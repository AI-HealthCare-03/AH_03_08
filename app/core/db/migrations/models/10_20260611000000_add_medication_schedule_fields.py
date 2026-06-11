from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `medications`
            ADD COLUMN `start_date` DATE NULL,
            ADD COLUMN `end_date` DATE NULL,
            ADD COLUMN `interval_days` INT NULL;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `medications`
            DROP COLUMN `start_date`,
            DROP COLUMN `end_date`,
            DROP COLUMN `interval_days`;
    """