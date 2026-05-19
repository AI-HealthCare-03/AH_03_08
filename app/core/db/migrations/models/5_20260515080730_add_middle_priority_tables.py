from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `calendar_events` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `event_date` DATE NOT NULL,
    `scheduled_time` TIME(6) NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    `taken_at` DATETIME(6),
    `note` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `medication_id` CHAR(36) NOT NULL,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_calendar_medicati_1ec8c964` FOREIGN KEY (`medication_id`) REFERENCES `medications` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_calendar_users_e2465c56` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `notifications` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `title` VARCHAR(200) NOT NULL,
    `type` VARCHAR(50) NOT NULL,
    `scheduled_time` TIME(6) NOT NULL,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `medication_id` CHAR(36) NOT NULL,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_notifica_medicati_66677a7a` FOREIGN KEY (`medication_id`) REFERENCES `medications` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_notifica_users_ca29871f` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `guide_assets` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `asset_type` VARCHAR(50) NOT NULL,
    `file_url` VARCHAR(500) NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `guide_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_guide_as_guides_234bde75` FOREIGN KEY (`guide_id`) REFERENCES `guides` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `feedbacks` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `rating` INT NOT NULL,
    `comment` LONGTEXT,
    `status` VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    `deactive_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `deactive_by_id` BIGINT,
    `guide_id` CHAR(36) NOT NULL,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_feedback_users_9a69e162` FOREIGN KEY (`deactive_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_feedback_guides_522ec30a` FOREIGN KEY (`guide_id`) REFERENCES `guides` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_feedback_users_fcbb7783` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `feedback_tags` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `type` VARCHAR(50) NOT NULL,
    `label` VARCHAR(100) NOT NULL,
    `display_order` INT NOT NULL DEFAULT 0
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `feedback_tag_selections` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `feedback_id` CHAR(36) NOT NULL,
    `tag_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_feedback_feedback_6a4342eb` FOREIGN KEY (`feedback_id`) REFERENCES `feedbacks` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_feedback_feedback_ddc9327f` FOREIGN KEY (`tag_id`) REFERENCES `feedback_tags` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `feedbacks`;
        DROP TABLE IF EXISTS `feedback_tag_selections`;
        DROP TABLE IF EXISTS `calendar_events`;
        DROP TABLE IF EXISTS `notifications`;
        DROP TABLE IF EXISTS `guide_assets`;
        DROP TABLE IF EXISTS `feedback_tags`;"""


MODELS_STATE = (
    "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"
    "q4tf9nYdPjXn7f8iM7xv"
)
