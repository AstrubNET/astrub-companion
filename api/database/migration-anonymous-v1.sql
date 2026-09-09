ALTER TABLE `companion_price_events`
    MODIFY COLUMN `token_id` bigint(20) unsigned NULL,
    MODIFY COLUMN `user_id` bigint(20) unsigned NULL,
    MODIFY COLUMN `event_kind` enum('listing','purchase','price_update','market_view') NOT NULL,
    ADD COLUMN `device_hash` binary(32) NULL AFTER `user_id`,
    ADD KEY `idx_companion_device_rate` (`device_hash`, `received_at`);
