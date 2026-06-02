from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `users` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `email` VARCHAR(40) NOT NULL,
    `hashed_password` VARCHAR(128) NOT NULL,
    `name` VARCHAR(20) NOT NULL,
    `gender` VARCHAR(6) NOT NULL COMMENT 'MALE: MALE\nFEMALE: FEMALE',
    `birth_date` DATE NOT NULL,
    `phone_number` VARCHAR(11) NOT NULL,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `is_admin` BOOL NOT NULL DEFAULT 0,
    `last_login` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `height_cm` DOUBLE,
    `weight_kg` DOUBLE,
    `oauth_provider` VARCHAR(20),
    `oauth_id` VARCHAR(100)
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `medical_records` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `record_type` INT NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    `ocr_raw_text` LONGTEXT,
    `parsed_data` JSON,
    `file_url` VARCHAR(500),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_medical__users_aa3196ba` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `guides` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `status` VARCHAR(20) NOT NULL DEFAULT 'processing',
    `title` VARCHAR(200),
    `medication_guide` LONGTEXT,
    `lifestyle_guide` LONGTEXT,
    `summary_text` LONGTEXT,
    `allergy_warnings` JSON NOT NULL,
    `condition_interactions` JSON NOT NULL,
    `prompt_version` VARCHAR(20) NOT NULL DEFAULT 'v1.0',
    `llm_model` VARCHAR(100),
    `llm_temperature` DOUBLE,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `record_id` CHAR(36) NOT NULL,
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_guides_medical__532b52ea` FOREIGN KEY (`record_id`) REFERENCES `medical_records` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_guides_users_73e91131` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='복약 가이드 정규 모델 (app/models/guides.py 단일 정의).';
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
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `guide_assets` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `asset_type` VARCHAR(50) NOT NULL,
    `file_url` VARCHAR(500),
    `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `guide_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_guide_as_guides_234bde75` FOREIGN KEY (`guide_id`) REFERENCES `guides` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `allergies` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `allergy_name` VARCHAR(200) NOT NULL,
    `severity` VARCHAR(50),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_allergie_users_cc13c577` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `underlying_diseases` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `underlying_disease_name` VARCHAR(200) NOT NULL,
    `severity` VARCHAR(50),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_underlyi_users_0044808f` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
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
        CREATE TABLE IF NOT EXISTS `feedbacks` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `rating` INT NOT NULL,
    `tag_ids` JSON NOT NULL,
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
) CHARACTER SET utf8mb4;
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
        DROP TABLE IF EXISTS `underlying_diseases`;
        DROP TABLE IF EXISTS `feedback_tag_selections`;
        DROP TABLE IF EXISTS `audit_logs`;
        DROP TABLE IF EXISTS `calendar_events`;
        DROP TABLE IF EXISTS `chat_messages`;
        DROP TABLE IF EXISTS `medications`;
        DROP TABLE IF EXISTS `model_metrics`;
        DROP TABLE IF EXISTS `chat_sessions`;
        DROP TABLE IF EXISTS `guides`;
        DROP TABLE IF EXISTS `feedbacks`;
        DROP TABLE IF EXISTS `medical_records`;
        DROP TABLE IF EXISTS `access_logs`;
        DROP TABLE IF EXISTS `users`;
        DROP TABLE IF EXISTS `error_logs`;
        DROP TABLE IF EXISTS `metric_snapshots`;
        DROP TABLE IF EXISTS `feedback_tags`;
        DROP TABLE IF EXISTS `allergies`;
        DROP TABLE IF EXISTS `guide_assets`;
        DROP TABLE IF EXISTS `notifications`;"""


MODELS_STATE = (
    "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"
)
