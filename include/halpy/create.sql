DROP TABLE IF EXISTS `backward`;
DROP TABLE IF EXISTS `forward`;
DROP TABLE IF EXISTS `words`;

CREATE TABLE `words` (
    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `word` tinyblob,
    `symbol` int(10) unsigned NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `no_dupe_symbols` (`symbol`),
    UNIQUE KEY `no_dupe_words` (`word`(10))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;

LOCK TABLES `words` WRITE;
INSERT INTO `words` VALUES (1,'<ERROR>',0),(2,'<FIN>',1);
UNLOCK TABLES;

CREATE TABLE `backward` (
    `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `symbol` int(10) unsigned NOT NULL,
    `usage` int(10) unsigned NOT NULL DEFAULT '0',
    `count` int(10) unsigned NOT NULL DEFAULT '0',
    `parent` int(10) unsigned DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `no_dupe_symbols` (`symbol`,`parent`),
    KEY `tree` (`id`,`parent`),
    CONSTRAINT `bkeys` FOREIGN KEY (`symbol`) REFERENCES `words` (`symbol`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

LOCK TABLES `backward` WRITE;
INSERT INTO `backward` VALUES (1,0,0,0,NULL);
UNLOCK TABLES;

CREATE TABLE `forward` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `symbol` int(10) unsigned NOT NULL,
  `usage` int(10) unsigned NOT NULL DEFAULT '0',
  `count` int(10) unsigned NOT NULL DEFAULT '0',
  `parent` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `no_dupe_symbols` (`symbol`,`parent`),
  KEY `tree` (`id`,`parent`),
  CONSTRAINT `fkeys` FOREIGN KEY (`symbol`) REFERENCES `words` (`symbol`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

LOCK TABLES `forward` WRITE;
INSERT INTO `forward` VALUES (1,0,0,0,NULL);
UNLOCK TABLES;
