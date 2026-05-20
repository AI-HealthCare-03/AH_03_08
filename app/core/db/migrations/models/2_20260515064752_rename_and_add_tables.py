from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
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
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `medications`;
        DROP TABLE IF EXISTS `underlying_diseases`;
        DROP TABLE IF EXISTS `allergies`;"""
