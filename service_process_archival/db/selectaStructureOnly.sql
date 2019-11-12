CREATE DATABASE  IF NOT EXISTS `selectadb` /*!40100 DEFAULT CHARACTER SET big5 */;
USE `selectadb`;
-- MySQL dump 10.13  Distrib 5.7.17, for macos10.12 (x86_64)
--
-- Host: 127.0.0.1    Database: selectadb
-- ------------------------------------------------------
-- Server version	5.7.19

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
-- Table structure for table `account`
--

DROP TABLE IF EXISTS `account`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `account` (
  `account_id` varchar(64) NOT NULL DEFAULT '',
  `email` varchar(255) DEFAULT NULL,
  `password` varchar(64) NOT NULL,
  `account_type` varchar(64) NOT NULL,
  PRIMARY KEY (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cv_pipelines`
--

DROP TABLE IF EXISTS `cv_pipelines`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cv_pipelines` (
  `pipeline_id` int(11) NOT NULL,
  `pipline_name` varchar(200) DEFAULT NULL,
  `pipeline_desc` varchar(1000) DEFAULT NULL,
  `pipeline_properties` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`pipeline_id`),
  UNIQUE KEY `pipline_name_UNIQUE` (`pipline_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `process_attributes`
--

DROP TABLE IF EXISTS `process_attributes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `process_attributes` (
  `process_id` varchar(100) DEFAULT NULL,
  `attribute_key` varchar(100) DEFAULT NULL,
  `attribute_value` varchar(200) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `process_report`
--

DROP TABLE IF EXISTS `process_report`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `process_report` (
  `study_accession` varchar(45) NOT NULL COMMENT 'Study id of the analysis',
  `datahub` varchar(45) NOT NULL COMMENT 'Dcc hub account ',
  `run_accession` varchar(45) DEFAULT NULL COMMENT 'Run id of the analysis',
  `process_id` varchar(45) NOT NULL,
  `selection_id` int(11) NOT NULL,
  `analysis_id` varchar(45) DEFAULT NULL,
  `process_report_start_time` datetime DEFAULT NULL,
  `process_report_end_time` datetime DEFAULT NULL,
  `process_report_id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`process_report_id`)
) ENGINE=InnoDB AUTO_INCREMENT=923 DEFAULT CHARSET=big5;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `process_selection`
--

DROP TABLE IF EXISTS `process_selection`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `process_selection` (
  `selection_id` int(11) NOT NULL AUTO_INCREMENT,
  `datahub` varchar(100) DEFAULT NULL,
  `tax_id` int(11) DEFAULT NULL,
  `study_accession` varchar(45) DEFAULT NULL,
  `run_accession` varchar(45) DEFAULT NULL,
  `pipeline_name` varchar(200) NOT NULL,
  `analysis_id` varchar(45) DEFAULT NULL,
  `public` varchar(45) DEFAULT NULL,
  `selection_provided_date` datetime DEFAULT NULL,
  `selection_to_attribute_start` datetime DEFAULT NULL,
  `selection_to_attribute_end` datetime DEFAULT NULL,
  `selection_to_attribute_error` varchar(500) DEFAULT NULL,
  `audit_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `audit_user` varchar(45) DEFAULT NULL,
  `webin` varchar(100) NOT NULL,
  `process_type` varchar(45) DEFAULT NULL COMMENT 'Instruct at what level of the hierarchy to run the analysis from broader to more specific (DATAHUB , STUDY_ID, RUN_ID)',
  PRIMARY KEY (`selection_id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `process_stages`
--

DROP TABLE IF EXISTS `process_stages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `process_stages` (
  `process_id` varchar(100) NOT NULL,
  `stage_name` varchar(100) NOT NULL,
  `selection_id` int(11) NOT NULL,
  `audit_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `audit_user` varchar(100) DEFAULT NULL,
  `stage_start` datetime DEFAULT NULL,
  `stage_end` datetime DEFAULT NULL,
  `stage_error` text,
  PRIMARY KEY (`process_id`,`stage_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `selecta_rule_templates`
--

DROP TABLE IF EXISTS `selecta_rule_templates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `selecta_rule_templates` (
  `template_id` int(11) NOT NULL,
  `pipeline_id` varchar(45) DEFAULT NULL,
  `template` varchar(45) DEFAULT NULL,
  `master_attributes` varchar(45) DEFAULT NULL,
  `all_attributes` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`template_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping events for database 'selectadb'
--

--
-- Dumping routines for database 'selectadb'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-09-25 16:45:57
