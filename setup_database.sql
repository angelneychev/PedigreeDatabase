-- SQL script to create the pedigree_db database in MariaDB
-- Run this script in your MariaDB client before starting the application

-- Create the database
CREATE DATABASE IF NOT EXISTS pedigree_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create a user for the application (optional, you can use root)
-- CREATE USER IF NOT EXISTS 'pedigree_user'@'localhost' IDENTIFIED BY 'pedigree_password';
-- GRANT ALL PRIVILEGES ON pedigree_db.* TO 'pedigree_user'@'localhost';
-- FLUSH PRIVILEGES;

-- Use the database
USE pedigree_db;

-- The tables will be created automatically by SQLAlchemy when the application starts
