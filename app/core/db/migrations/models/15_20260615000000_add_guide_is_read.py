from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `guides`
            ADD `is_read` BOOL NOT NULL DEFAULT 0,
            ADD `read_at` DATETIME(6) NULL;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `guides`
            DROP COLUMN `is_read`,
            DROP COLUMN `read_at`;
    """