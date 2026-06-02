from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `guides` ADD `drug_interactions` JSON NOT NULL DEFAULT (JSON_ARRAY());
        ALTER TABLE `guides` ADD `side_effects_watch` JSON NOT NULL DEFAULT (JSON_ARRAY());
        ALTER TABLE `guides` ADD `medication_schedule` JSON NOT NULL DEFAULT (JSON_ARRAY());
        ALTER TABLE `guides` ADD `urgent_warnings` JSON NOT NULL DEFAULT (JSON_ARRAY());"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `guides` DROP COLUMN `drug_interactions`;
        ALTER TABLE `guides` DROP COLUMN `side_effects_watch`;
        ALTER TABLE `guides` DROP COLUMN `medication_schedule`;
        ALTER TABLE `guides` DROP COLUMN `urgent_warnings`;"""
