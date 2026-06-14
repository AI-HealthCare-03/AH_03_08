from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> None:
    await db.execute_script("""
        ALTER TABLE `guides` ADD `drug_interactions` JSON NOT NULL DEFAULT (JSON_ARRAY());
        ALTER TABLE `guides` ADD `side_effects_watch` JSON NOT NULL DEFAULT (JSON_ARRAY());
        ALTER TABLE `guides` ADD `medication_schedule` JSON NOT NULL DEFAULT (JSON_ARRAY());
        ALTER TABLE `guides` ADD `urgent_warnings` JSON NOT NULL DEFAULT (JSON_ARRAY());""")


async def downgrade(db: BaseDBAsyncClient) -> None:
    await db.execute_script("""
        ALTER TABLE `guides` DROP COLUMN `drug_interactions`;
        ALTER TABLE `guides` DROP COLUMN `side_effects_watch`;
        ALTER TABLE `guides` DROP COLUMN `medication_schedule`;
        ALTER TABLE `guides` DROP COLUMN `urgent_warnings`;""")


MODELS_STATE = (
    "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"
    "/n/erWTF"
)
