from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `chat_sessions` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `title` VARCHAR(200),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `last_active_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `guide_id` CHAR(36),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_chat_ses_guides_68cc1481` FOREIGN KEY (`guide_id`) REFERENCES `guides` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_chat_ses_users_520002c0` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `chat_messages` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `role` VARCHAR(20) NOT NULL,
    `content` LONGTEXT NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `session_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_chat_mes_chat_ses_0d4a2737` FOREIGN KEY (`session_id`) REFERENCES `chat_sessions` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `chat_messages`;
        DROP TABLE IF EXISTS `chat_sessions`;"""


MODELS_STATE = (
    "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"
)
