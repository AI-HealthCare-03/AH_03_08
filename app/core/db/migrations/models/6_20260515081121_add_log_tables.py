from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `access_logs` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `method` VARCHAR(10) NOT NULL,
    `endpoint` VARCHAR(500) NOT NULL,
    `status_code` INT NOT NULL,
    `latency_ms` INT,
    `request_body` LONGTEXT,
    `response_body` LONGTEXT,
    `ip_address` VARCHAR(50),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT,
    CONSTRAINT `fk_access_l_users_a95fbdb7` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `error_logs` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `status_code` INT NOT NULL,
    `error_type` VARCHAR(100),
    `message` LONGTEXT,
    `stack_trace` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `access_log_id` CHAR(36),
    CONSTRAINT `fk_error_lo_access_l_aba37c57` FOREIGN KEY (`access_log_id`) REFERENCES `access_logs` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `action` VARCHAR(100) NOT NULL,
    `target_type` VARCHAR(100) NOT NULL,
    `target_id` CHAR(36),
    `before_value` JSON,
    `after_value` JSON,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `actor_id` BIGINT,
    CONSTRAINT `fk_audit_lo_users_7e2888de` FOREIGN KEY (`actor_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `metric_snapshots` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `model_type` VARCHAR(100) NOT NULL,
    `snapshot_date` DATE NOT NULL,
    `avg_latency_ms` DOUBLE,
    `success_rate` DOUBLE,
    `avg_rating` DOUBLE,
    `total_count` INT NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `model_metrics` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `model_type` VARCHAR(100) NOT NULL,
    `latency_ms` DOUBLE,
    `token_input` INT,
    `token_output` INT,
    `confidence_score` DOUBLE,
    `success` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `reference_id` CHAR(36),
    CONSTRAINT `fk_model_me_guides_9d0aaa6f` FOREIGN KEY (`reference_id`) REFERENCES `guides` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `metric_snapshots`;
        DROP TABLE IF EXISTS `model_metrics`;
        DROP TABLE IF EXISTS `error_logs`;
        DROP TABLE IF EXISTS `audit_logs`;
        DROP TABLE IF EXISTS `access_logs`;"""


MODELS_STATE = (
    "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"
    "JV9cTn9oauxPGx+/DVj/8DE/suDg=="
)
