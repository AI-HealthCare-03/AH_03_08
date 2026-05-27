from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `guides` ADD `record_id` CHAR(36) NOT NULL;
        ALTER TABLE `guides` DROP COLUMN `medical_record_id`;
        ALTER TABLE `guides` MODIFY COLUMN `allergy_warnings` JSON NOT NULL;
        ALTER TABLE `guides` MODIFY COLUMN `condition_interactions` JSON NOT NULL;
        ALTER TABLE `medical_records` ADD `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6);
        ALTER TABLE `medical_records` ADD `file_url` VARCHAR(500);
        ALTER TABLE `medical_records` ALTER COLUMN `record_type` DROP DEFAULT;
        ALTER TABLE `guides` ADD CONSTRAINT `fk_guides_medical__532b52ea` FOREIGN KEY (`record_id`) REFERENCES `medical_records` (`id`) ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `guides` DROP FOREIGN KEY `fk_guides_medical__532b52ea`;
        ALTER TABLE `users` RENAME COLUMN `birth_date` TO `birthday`;
        ALTER TABLE `guides` ADD `medical_record_id` CHAR(36) NOT NULL;
        ALTER TABLE `guides` DROP COLUMN `record_id`;
        ALTER TABLE `guides` MODIFY COLUMN `allergy_warnings` JSON;
        ALTER TABLE `guides` MODIFY COLUMN `condition_interactions` JSON;
        ALTER TABLE `medical_records` DROP COLUMN `updated_at`;
        ALTER TABLE `medical_records` DROP COLUMN `file_url`;
        ALTER TABLE `medical_records` ALTER COLUMN `record_type` SET DEFAULT 0;
        ALTER TABLE `guides` ADD CONSTRAINT `fk_guides_medical__ae6ee5f5` FOREIGN KEY (`medical_record_id`) REFERENCES `medical_records` (`id`) ON DELETE CASCADE;"""


MODELS_STATE = (
    "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"
    "R2QDMaymOz63N34l9o/9h69+/B9JnHOz"
)
from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return "SELECT 1;"


async def downgrade(db: BaseDBAsyncClient) -> str:
    return "SELECT 1;"

