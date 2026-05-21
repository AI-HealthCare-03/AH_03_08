from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `medical_records` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `record_type` VARCHAR(20) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    `parsed_data` JSON,
    `file_url` VARCHAR(500),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_medical_r_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS `guides` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `status` VARCHAR(12) NOT NULL COMMENT 'PENDING: PENDING\nPROCESSING: PROCESSING\nDONE: DONE\nFAILED: FAILED',
    `medication_guide` LONGTEXT,
    `lifestyle_guide` LONGTEXT,
    `summary` LONGTEXT,
    `allergy_warnings` JSON NOT NULL,
    `condition_interactions` JSON NOT NULL,
    `completed_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    `record_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_guides_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_guides_medical_records_record_id` FOREIGN KEY (`record_id`) REFERENCES `medical_records` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS `guide_assets` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `asset_type` VARCHAR(20) NOT NULL,
    `file_url` VARCHAR(500),
    `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `guide_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_guide_assets_guides_guide_id` FOREIGN KEY (`guide_id`) REFERENCES `guides` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS `chat_sessions` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_chat_sessions_users_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS `chat_messages` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `role` VARCHAR(10) NOT NULL,
    `content` LONGTEXT NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'DONE',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `session_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_chat_messages_chat_sessions_session_id` FOREIGN KEY (`session_id`) REFERENCES `chat_sessions` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `chat_messages`;
        DROP TABLE IF EXISTS `chat_sessions`;
        DROP TABLE IF EXISTS `guide_assets`;
        DROP TABLE IF EXISTS `guides`;
        DROP TABLE IF EXISTS `medical_records`;"""
