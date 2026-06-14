from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users`
            ADD COLUMN `is_email_verified` BOOL NOT NULL DEFAULT 0,
            ADD COLUMN `email_verify_token` VARCHAR(64) NULL;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users`
            DROP COLUMN `is_email_verified`,
            DROP COLUMN `email_verify_token`;
    """
