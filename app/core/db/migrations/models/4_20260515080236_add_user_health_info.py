from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users` ADD `height_cm` DOUBLE;
        ALTER TABLE `users` ADD `weight_kg` DOUBLE;
        ALTER TABLE `users` ADD `oauth_id` VARCHAR(100);
        ALTER TABLE `users` ADD `oauth_provider` VARCHAR(20);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `users` DROP COLUMN `height_cm`;
        ALTER TABLE `users` DROP COLUMN `weight_kg`;
        ALTER TABLE `users` DROP COLUMN `oauth_id`;
        ALTER TABLE `users` DROP COLUMN `oauth_provider`;"""


MODELS_STATE = (
    "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"
    "kd2X1G/Pl/pxw8XQ=="
)
