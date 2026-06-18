from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users` ADD `google_access_token` LONGTEXT;
        ALTER TABLE `users` ADD `google_refresh_token` LONGTEXT;
        ALTER TABLE `users` ADD `google_token_expiry` DATETIME(6);
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users` DROP COLUMN `google_access_token`;
        ALTER TABLE `users` DROP COLUMN `google_refresh_token`;
        ALTER TABLE `users` DROP COLUMN `google_token_expiry`;
    """
