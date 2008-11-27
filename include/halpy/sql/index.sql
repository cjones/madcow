ALTER TABLE `words` ADD INDEX (`string`);
ALTER TABLE `forward` ADD INDEX (`word_id`, `parent_id`);
ALTER TABLE `backward` ADD INDEX (`word_id`, `parent_id`);
