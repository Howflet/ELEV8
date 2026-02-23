-- MySQL dump 10.13  Distrib 8.0.19, for Win64 (x86_64)
--
-- Host: localhost    Database: elev8
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `elevatorstate`
--

DROP TABLE IF EXISTS `elevatorstate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `elevatorstate` (
  `elevator_id` int NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `state` varchar(50) DEFAULT NULL,
  `direction` varchar(10) DEFAULT NULL,
  `current_floor` int DEFAULT NULL,
  `target_floor` int DEFAULT NULL,
  `last_updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`elevator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `elevatorstate`
--

LOCK TABLES `elevatorstate` WRITE;
/*!40000 ALTER TABLE `elevatorstate` DISABLE KEYS */;
/*!40000 ALTER TABLE `elevatorstate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `requests`
--

DROP TABLE IF EXISTS `requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `requests` (
  `user_id` varchar(40) NOT NULL,
  `source_floor` int DEFAULT NULL,
  `destination_floor` int DEFAULT NULL,
  `timestamp` timestamp NULL DEFAULT NULL,
  `status` varchar(28) DEFAULT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `requests`
--

LOCK TABLES `requests` WRITE;
/*!40000 ALTER TABLE `requests` DISABLE KEYS */;
/*!40000 ALTER TABLE `requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `campus_id` int NOT NULL,
  `password` varchar(255) NOT NULL,
  `access_level` int DEFAULT NULL,
  PRIMARY KEY (`campus_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1001,'$2a$12$l2Xp5Xp5Xp5Xp5Xp5Xp5Xuq6Xp5Xp5Xp5Xp5Xp5Xp5Xp5Xp5Xp5',3),(1002,'$2a$12$k3Yq6Yq6Yq6Yq6Yq6Yq6Yue7Yq6Yq6Yq6Yq6Yq6Yq6Yq6Yq6Yq6',2),(1003,'$2a$12$m4Zr7Zr7Zr7Zr7Zr7Zr7Zuf8Zr7Zr7Zr7Zr7Zr7Zr7Zr7Zr7Zr7',1),(25674212,'$2a$12$IysxXBe2Bs1000HszBYsQucXuTsC.vXwwqooKcRCxwS3i058scjGq',3),(27830129,'$2a$12$OQVLphJAftxycUVy4S6qmueXSOk7oDFMHqdTfdVobe6bpxtLCBIKW',2),(28374616,'$2a$12$oVf2as7h72udUE5yC6CDaeTWGDpu6vuLPvKQBmCoWXHVVugxQxuea',1),(31947594,'$2a$12$/E5wUp6eD7zw5tJrmsOPAOt7mg13.zfRQuMzB6H1dQwqRlpaOsXE6',5),(213234567,'$2a$12$KW2XMo2hQUIXst1lQlSep.IBu/7dkb41mKqSARTnXt/5JGbQpPwuq',4);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'elev8'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-14 20:12:12
