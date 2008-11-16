-- MySQL dump 10.13  Distrib 5.1.29-rc, for portbld-freebsd6.4 (i386)
--
-- Host: localhost    Database: tree
-- ------------------------------------------------------
-- Server version	5.1.29-rc

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `backward`
--

DROP TABLE IF EXISTS `backward`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `backward` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `word` int(10) unsigned NOT NULL,
  `usage` int(10) unsigned NOT NULL DEFAULT '0',
  `count` int(10) unsigned NOT NULL DEFAULT '0',
  `parent` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `word` (`word`,`parent`),
  KEY `id` (`id`,`parent`),
  KEY `word_2` (`word`),
  KEY `parent` (`parent`),
  CONSTRAINT `backward_ibfk_1` FOREIGN KEY (`word`) REFERENCES `words` (`id`),
  CONSTRAINT `backward_ibfk_2` FOREIGN KEY (`parent`) REFERENCES `backward` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `backward`
--

LOCK TABLES `backward` WRITE;
/*!40000 ALTER TABLE `backward` DISABLE KEYS */;
INSERT INTO `backward` VALUES (1,1,0,0,NULL);
/*!40000 ALTER TABLE `backward` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forward`
--

DROP TABLE IF EXISTS `forward`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `forward` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `word` int(10) unsigned NOT NULL,
  `usage` int(10) unsigned NOT NULL DEFAULT '0',
  `count` int(10) unsigned NOT NULL DEFAULT '0',
  `parent` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `word` (`word`,`parent`),
  KEY `id` (`id`,`parent`),
  KEY `word_2` (`word`),
  KEY `parent` (`parent`),
  CONSTRAINT `forward_ibfk_1` FOREIGN KEY (`word`) REFERENCES `words` (`id`),
  CONSTRAINT `forward_ibfk_2` FOREIGN KEY (`parent`) REFERENCES `forward` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `forward`
--

LOCK TABLES `forward` WRITE;
/*!40000 ALTER TABLE `forward` DISABLE KEYS */;
INSERT INTO `forward` VALUES (1,1,0,0,NULL);
/*!40000 ALTER TABLE `forward` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `words`
--

DROP TABLE IF EXISTS `words`;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
CREATE TABLE `words` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `word` tinyblob,
  PRIMARY KEY (`id`),
  UNIQUE KEY `word` (`word`(10)),
  KEY `id` (`id`,`word`(10))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
SET character_set_client = @saved_cs_client;

--
-- Dumping data for table `words`
--

LOCK TABLES `words` WRITE;
/*!40000 ALTER TABLE `words` DISABLE KEYS */;
INSERT INTO `words` VALUES (1,'<ERROR>'),(2,'<FIN>');
/*!40000 ALTER TABLE `words` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2008-11-16  9:24:55
