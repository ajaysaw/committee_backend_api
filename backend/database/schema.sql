-- ============================================================
-- Committee / Chit Fund Management Platform
-- MySQL Database Schema - 35 Tables
-- Database: committee
-- ============================================================

CREATE DATABASE IF NOT EXISTS `committee`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `committee`;

-- ── 1. users ─────────────────────────────────────────────
CREATE TABLE `users` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `phone` VARCHAR(20) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('admin','member') NOT NULL DEFAULT 'member',
    `status` ENUM('active','inactive','suspended','pending') NOT NULL DEFAULT 'pending',
    `avatar_url` VARCHAR(500) NULL,
    `address` TEXT NULL,
    `city` VARCHAR(100) NULL,
    `state` VARCHAR(100) NULL,
    `pincode` VARCHAR(10) NULL,
    `is_verified` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    INDEX `idx_users_email` (`email`),
    INDEX `idx_users_phone` (`phone`)
) ENGINE=InnoDB;

-- ── 2. user_profiles ─────────────────────────────────────
CREATE TABLE `user_profiles` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL UNIQUE,
    `date_of_birth` DATE NULL,
    `gender` VARCHAR(20) NULL,
    `occupation` VARCHAR(255) NULL,
    `aadhar_number` VARCHAR(20) NULL,
    `pan_number` VARCHAR(20) NULL,
    `bank_name` VARCHAR(255) NULL,
    `bank_account_number` VARCHAR(50) NULL,
    `bank_ifsc` VARCHAR(20) NULL,
    `upi_id` VARCHAR(100) NULL,
    `emergency_contact_name` VARCHAR(255) NULL,
    `emergency_contact_phone` VARCHAR(20) NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 3. user_sessions ─────────────────────────────────────
CREATE TABLE `user_sessions` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `token` VARCHAR(500) NOT NULL,
    `refresh_token` VARCHAR(500) NULL,
    `device_info` VARCHAR(500) NULL,
    `ip_address` VARCHAR(45) NULL,
    `expires_at` DATETIME NOT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    INDEX `idx_sessions_token` (`token`(255)),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 4. otp_verifications ─────────────────────────────────
CREATE TABLE `otp_verifications` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `otp_code` VARCHAR(10) NOT NULL,
    `otp_type` VARCHAR(50) NOT NULL,
    `expires_at` DATETIME NOT NULL,
    `is_used` TINYINT(1) NOT NULL DEFAULT 0,
    `attempts` INT NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 5. committees ────────────────────────────────────────
CREATE TABLE `committees` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `description` TEXT NULL,
    `committee_type` ENUM('lucky_draw','bidding','percentage') NOT NULL,
    `status` ENUM('draft','active','completed','cancelled') NOT NULL DEFAULT 'draft',
    `created_by` BIGINT NOT NULL,
    `total_members` INT NOT NULL,
    `monthly_contribution` DECIMAL(12,2) NOT NULL,
    `total_amount` DECIMAL(14,2) NOT NULL,
    `duration_months` INT NOT NULL,
    `start_date` DATE NULL,
    `end_date` DATE NULL,
    `current_round` INT NOT NULL DEFAULT 0,
    `interest_rate` DECIMAL(5,2) DEFAULT 0.00,
    `min_bid_amount` DECIMAL(12,2) NULL,
    `max_bid_amount` DECIMAL(12,2) NULL,
    `rules` TEXT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    INDEX `idx_committee_type` (`committee_type`),
    INDEX `idx_committee_status` (`status`),
    FOREIGN KEY (`created_by`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

-- ── 6. committee_settings ────────────────────────────────
CREATE TABLE `committee_settings` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `committee_id` BIGINT NOT NULL,
    `setting_key` VARCHAR(100) NOT NULL,
    `setting_value` TEXT NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    UNIQUE KEY `uq_committee_setting` (`committee_id`, `setting_key`),
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 7. committee_members ─────────────────────────────────
CREATE TABLE `committee_members` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `committee_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `slot_number` INT NULL,
    `membership_status` ENUM('pending','approved','rejected','left','removed') NOT NULL DEFAULT 'pending',
    `has_received_payout` TINYINT(1) NOT NULL DEFAULT 0,
    `payout_round` INT NULL,
    `total_paid` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `total_received` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `joined_at` DATETIME NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    UNIQUE KEY `uq_committee_user` (`committee_id`, `user_id`),
    INDEX `idx_member_status` (`membership_status`),
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 8. committee_rounds ──────────────────────────────────
CREATE TABLE `committee_rounds` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `committee_id` BIGINT NOT NULL,
    `round_number` INT NOT NULL,
    `status` ENUM('pending','in_progress','completed','cancelled') NOT NULL DEFAULT 'pending',
    `scheduled_date` DATE NULL,
    `completed_date` DATE NULL,
    `pool_amount` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `winner_member_id` BIGINT NULL,
    `winner_amount` DECIMAL(14,2) NULL,
    `discount_amount` DECIMAL(12,2) DEFAULT 0.00,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    UNIQUE KEY `uq_committee_round` (`committee_id`, `round_number`),
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`winner_member_id`) REFERENCES `committee_members`(`id`)
) ENGINE=InnoDB;

-- ── 9. bids ──────────────────────────────────────────────
CREATE TABLE `bids` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `round_id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `committee_id` BIGINT NOT NULL,
    `bid_amount` DECIMAL(12,2) NOT NULL,
    `is_winner` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    INDEX `idx_bid_round` (`round_id`),
    FOREIGN KEY (`round_id`) REFERENCES `committee_rounds`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 10. bid_settings ─────────────────────────────────────
CREATE TABLE `bid_settings` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `committee_id` BIGINT NOT NULL UNIQUE,
    `min_bid_percentage` DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    `max_bid_percentage` DECIMAL(5,2) NOT NULL DEFAULT 100.00,
    `bid_increment` DECIMAL(10,2) NOT NULL DEFAULT 100.00,
    `auto_close_minutes` INT NOT NULL DEFAULT 30,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 11. lucky_draws ──────────────────────────────────────
CREATE TABLE `lucky_draws` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `round_id` BIGINT NOT NULL UNIQUE,
    `committee_id` BIGINT NOT NULL,
    `winner_member_id` BIGINT NULL,
    `draw_seed` VARCHAR(255) NULL,
    `draw_timestamp` DATETIME NULL,
    `eligible_member_ids` TEXT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`round_id`) REFERENCES `committee_rounds`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`winner_member_id`) REFERENCES `committee_members`(`id`)
) ENGINE=InnoDB;

-- ── 12. lucky_draw_history ───────────────────────────────
CREATE TABLE `lucky_draw_history` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `lucky_draw_id` BIGINT NOT NULL,
    `member_id` BIGINT NOT NULL,
    `was_eligible` TINYINT(1) NOT NULL DEFAULT 1,
    `was_winner` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`lucky_draw_id`) REFERENCES `lucky_draws`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`member_id`) REFERENCES `committee_members`(`id`)
) ENGINE=InnoDB;

-- ── 13. payments ─────────────────────────────────────────
CREATE TABLE `payments` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `committee_id` BIGINT NOT NULL,
    `round_number` INT NOT NULL,
    `amount` DECIMAL(12,2) NOT NULL,
    `payment_status` ENUM('pending','paid','late','missed','partial') NOT NULL DEFAULT 'pending',
    `payment_method` ENUM('cash','bank_transfer','upi','cheque','online') NULL,
    `payment_date` DATETIME NULL,
    `due_date` DATE NOT NULL,
    `late_fee` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `reference_number` VARCHAR(100) NULL,
    `notes` TEXT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    INDEX `idx_payment_status` (`payment_status`),
    INDEX `idx_payment_user_committee` (`user_id`, `committee_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 14. payment_schedules ────────────────────────────────
CREATE TABLE `payment_schedules` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `committee_id` BIGINT NOT NULL,
    `round_number` INT NOT NULL,
    `due_date` DATE NOT NULL,
    `amount` DECIMAL(12,2) NOT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    UNIQUE KEY `uq_schedule_round` (`committee_id`, `round_number`),
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 15. transactions ─────────────────────────────────────
CREATE TABLE `transactions` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `committee_id` BIGINT NOT NULL,
    `transaction_type` ENUM('contribution','payout','dividend','interest','penalty','refund') NOT NULL,
    `amount` DECIMAL(14,2) NOT NULL,
    `balance_after` DECIMAL(14,2) NULL,
    `description` TEXT NULL,
    `reference_id` VARCHAR(100) NULL,
    `round_number` INT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    INDEX `idx_transaction_type` (`transaction_type`),
    INDEX `idx_transaction_user` (`user_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 16. dividends ────────────────────────────────────────
CREATE TABLE `dividends` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `round_id` BIGINT NOT NULL,
    `committee_id` BIGINT NOT NULL,
    `member_id` BIGINT NOT NULL,
    `amount` DECIMAL(12,2) NOT NULL,
    `is_paid` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`round_id`) REFERENCES `committee_rounds`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`member_id`) REFERENCES `committee_members`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 17. interest_distributions ───────────────────────────
CREATE TABLE `interest_distributions` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `committee_id` BIGINT NOT NULL,
    `round_id` BIGINT NOT NULL,
    `member_id` BIGINT NOT NULL,
    `principal_amount` DECIMAL(14,2) NOT NULL,
    `interest_rate` DECIMAL(5,2) NOT NULL,
    `interest_amount` DECIMAL(12,2) NOT NULL,
    `is_paid` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`round_id`) REFERENCES `committee_rounds`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`member_id`) REFERENCES `committee_members`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 18. payouts ──────────────────────────────────────────
CREATE TABLE `payouts` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `committee_id` BIGINT NOT NULL,
    `round_id` BIGINT NOT NULL,
    `member_id` BIGINT NOT NULL,
    `gross_amount` DECIMAL(14,2) NOT NULL,
    `discount_amount` DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    `net_amount` DECIMAL(14,2) NOT NULL,
    `payment_method` ENUM('cash','bank_transfer','upi','cheque','online') NULL,
    `is_processed` TINYINT(1) NOT NULL DEFAULT 0,
    `processed_at` DATETIME NULL,
    `reference_number` VARCHAR(100) NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`round_id`) REFERENCES `committee_rounds`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`member_id`) REFERENCES `committee_members`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 19. penalties ────────────────────────────────────────
CREATE TABLE `penalties` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `committee_id` BIGINT NOT NULL,
    `payment_id` BIGINT NULL,
    `penalty_type` VARCHAR(50) NOT NULL,
    `amount` DECIMAL(10,2) NOT NULL,
    `reason` TEXT NULL,
    `is_waived` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`payment_id`) REFERENCES `payments`(`id`)
) ENGINE=InnoDB;

-- ── 20. notifications ────────────────────────────────────
CREATE TABLE `notifications` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `message` TEXT NOT NULL,
    `notification_type` ENUM('payment_reminder','payment_received','bid_started','bid_won','lucky_draw_result','committee_joined','committee_started','payout_processed','general') NOT NULL,
    `is_read` TINYINT(1) NOT NULL DEFAULT 0,
    `reference_id` BIGINT NULL,
    `reference_type` VARCHAR(50) NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    INDEX `idx_notification_user` (`user_id`, `is_read`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 21. notification_settings ────────────────────────────
CREATE TABLE `notification_settings` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL UNIQUE,
    `push_enabled` TINYINT(1) NOT NULL DEFAULT 1,
    `email_enabled` TINYINT(1) NOT NULL DEFAULT 1,
    `sms_enabled` TINYINT(1) NOT NULL DEFAULT 0,
    `payment_reminders` TINYINT(1) NOT NULL DEFAULT 1,
    `bid_notifications` TINYINT(1) NOT NULL DEFAULT 1,
    `draw_notifications` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 22. audit_logs ───────────────────────────────────────
CREATE TABLE `audit_logs` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NULL,
    `action` ENUM('create','update','delete','login','logout','payment','payout','bid','draw') NOT NULL,
    `entity_type` VARCHAR(100) NOT NULL,
    `entity_id` BIGINT NULL,
    `old_values` TEXT NULL,
    `new_values` TEXT NULL,
    `ip_address` VARCHAR(45) NULL,
    `user_agent` VARCHAR(500) NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    INDEX `idx_audit_entity` (`entity_type`, `entity_id`),
    INDEX `idx_audit_user` (`user_id`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

-- ── 23. system_config ────────────────────────────────────
CREATE TABLE `system_config` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `config_key` VARCHAR(100) NOT NULL UNIQUE,
    `config_value` TEXT NOT NULL,
    `description` TEXT NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL
) ENGINE=InnoDB;

-- ── 24. system_logs ──────────────────────────────────────
CREATE TABLE `system_logs` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `level` VARCHAR(20) NOT NULL,
    `module` VARCHAR(100) NOT NULL,
    `message` TEXT NOT NULL,
    `stack_trace` TEXT NULL,
    `request_id` VARCHAR(100) NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL
) ENGINE=InnoDB;

-- ── 25. rate_limit_tracker ───────────────────────────────
CREATE TABLE `rate_limit_tracker` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `ip_address` VARCHAR(45) NOT NULL,
    `endpoint` VARCHAR(255) NOT NULL,
    `request_count` INT NOT NULL DEFAULT 1,
    `window_start` DATETIME NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    INDEX `idx_rate_limit_ip` (`ip_address`)
) ENGINE=InnoDB;

-- ── 26. committee_invitations ────────────────────────────
CREATE TABLE `committee_invitations` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `committee_id` BIGINT NOT NULL,
    `invited_by` BIGINT NOT NULL,
    `invited_user_id` BIGINT NULL,
    `invited_phone` VARCHAR(20) NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `expires_at` DATETIME NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`invited_by`) REFERENCES `users`(`id`),
    FOREIGN KEY (`invited_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

-- ── 27. committee_documents ──────────────────────────────
CREATE TABLE `committee_documents` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `committee_id` BIGINT NOT NULL,
    `uploaded_by` BIGINT NOT NULL,
    `document_type` VARCHAR(50) NOT NULL,
    `file_name` VARCHAR(255) NOT NULL,
    `file_url` VARCHAR(500) NOT NULL,
    `file_size` INT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`uploaded_by`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

-- ── 28. member_guarantors ────────────────────────────────
CREATE TABLE `member_guarantors` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `member_id` BIGINT NOT NULL,
    `guarantor_name` VARCHAR(255) NOT NULL,
    `guarantor_phone` VARCHAR(20) NOT NULL,
    `guarantor_address` TEXT NULL,
    `guarantor_id_proof` VARCHAR(500) NULL,
    `is_verified` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`member_id`) REFERENCES `committee_members`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 29. financial_summaries ──────────────────────────────
CREATE TABLE `financial_summaries` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `committee_id` BIGINT NOT NULL,
    `round_number` INT NOT NULL,
    `total_collected` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `total_paid_out` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `total_dividends` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `total_interest` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `total_penalties` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `balance` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 30. member_statements ────────────────────────────────
CREATE TABLE `member_statements` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `member_id` BIGINT NOT NULL,
    `committee_id` BIGINT NOT NULL,
    `total_contributions` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `total_payouts` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `total_dividends` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `total_interest_earned` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `total_penalties` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `net_profit_loss` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `last_updated_round` INT NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`member_id`) REFERENCES `committee_members`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 31. committee_analytics ──────────────────────────────
CREATE TABLE `committee_analytics` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `committee_id` BIGINT NOT NULL,
    `metric_name` VARCHAR(100) NOT NULL,
    `metric_value` DECIMAL(14,2) NOT NULL,
    `metric_date` DATE NOT NULL,
    `metadata_json` TEXT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    INDEX `idx_analytics_committee` (`committee_id`, `metric_name`),
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 32. dashboard_stats ──────────────────────────────────
CREATE TABLE `dashboard_stats` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `total_committees` INT NOT NULL DEFAULT 0,
    `active_committees` INT NOT NULL DEFAULT 0,
    `total_invested` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `total_earned` DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    `pending_payments` INT NOT NULL DEFAULT 0,
    `next_payment_date` DATE NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 33. fcm_tokens ───────────────────────────────────────
CREATE TABLE `fcm_tokens` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `token` VARCHAR(500) NOT NULL,
    `device_type` VARCHAR(20) NULL,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ── 34. report_exports ───────────────────────────────────
CREATE TABLE `report_exports` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `report_type` VARCHAR(50) NOT NULL,
    `committee_id` BIGINT NULL,
    `file_url` VARCHAR(500) NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `parameters_json` TEXT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`)
) ENGINE=InnoDB;

-- ── 35. support_tickets ──────────────────────────────────
CREATE TABLE `support_tickets` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NOT NULL,
    `committee_id` BIGINT NULL,
    `subject` VARCHAR(255) NOT NULL,
    `description` TEXT NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'open',
    `priority` VARCHAR(20) NOT NULL DEFAULT 'medium',
    `assigned_to` BIGINT NULL,
    `resolved_at` DATETIME NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `deleted_at` TIMESTAMP NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`committee_id`) REFERENCES `committees`(`id`),
    FOREIGN KEY (`assigned_to`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;

-- ── Default System Config ────────────────────────────────
INSERT INTO `system_config` (`config_key`, `config_value`, `description`) VALUES
('late_fee_per_day', '10.00', 'Late payment fee per day in INR'),
('max_bid_attempts', '5', 'Maximum number of bids per member per round'),
('otp_expiry_minutes', '5', 'OTP expiry in minutes'),
('min_committee_members', '2', 'Minimum number of members to start a committee'),
('default_currency', 'INR', 'Default currency for transactions');
