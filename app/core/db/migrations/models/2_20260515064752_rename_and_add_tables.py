from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `medical_records` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `ocr_raw_text` LONGTEXT,
    `parsed_data` JSON,
    `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    `record_type` INT NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_medical__users_aa3196ba` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `guides` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `medication_guide` LONGTEXT,
    `lifestyle_guide` LONGTEXT,
    `llm_model` VARCHAR(100),
    `llm_temperature` DOUBLE,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `medical_record_id` CHAR(36) NOT NULL,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_guides_medical__ae6ee5f5` FOREIGN KEY (`medical_record_id`) REFERENCES `medical_records` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_guides_users_73e91131` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `medications` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `drug_name` VARCHAR(200) NOT NULL,
    `dosage` VARCHAR(100),
    `frequency` VARCHAR(100),
    `instructions` LONGTEXT,
    `warnings` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `medical_record_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_medicati_medical__494c8c82` FOREIGN KEY (`medical_record_id`) REFERENCES `medical_records` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `underlying_diseases` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `underlying_disease_name` VARCHAR(200) NOT NULL,
    `severity` VARCHAR(50),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_underlyi_users_0044808f` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `allergies` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `allergy_name` VARCHAR(200) NOT NULL,
    `severity` VARCHAR(50),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_allergie_users_cc13c577` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        DROP TABLE IF EXISTS `ai_results`;
        DROP TABLE IF EXISTS `health_records`;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `guides`;
        DROP TABLE IF EXISTS `medications`;
        DROP TABLE IF EXISTS `allergies`;
        DROP TABLE IF EXISTS `underlying_diseases`;
        DROP TABLE IF EXISTS `medical_records`;"""


MODELS_STATE = (
    "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"
    "QvJn0x6YtJX0z6Ypt8sfv/AAZaY2w="
)
