from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `guides` ADD `status` VARCHAR(20) NOT NULL DEFAULT 'processing';
        ALTER TABLE `guides` ADD `prompt_version` VARCHAR(20) NOT NULL DEFAULT 'v1.0';
        ALTER TABLE `guides` ADD `condition_interactions` JSON;
        ALTER TABLE `guides` ADD `allergy_warnings` JSON;
        ALTER TABLE `guides` ADD `summary_text` LONGTEXT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `guides` DROP COLUMN `status`;
        ALTER TABLE `guides` DROP COLUMN `prompt_version`;
        ALTER TABLE `guides` DROP COLUMN `condition_interactions`;
        ALTER TABLE `guides` DROP COLUMN `allergy_warnings`;
        ALTER TABLE `guides` DROP COLUMN `summary_text`;"""


MODELS_STATE = (
    "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"
    "G1yhBpIXJV98Tn7oauxPHx9uGrH/8HTXRs3Q=="
)
