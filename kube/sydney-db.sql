CREATE DATABASE sydney;

USE sydney;

CREATE TABLE messages
(
id int NOT NULL AUTO_INCREMENT,
message varchar(255) NOT NULL,
PRIMARY KEY (ID)
);

INSERT INTO messages (message) VALUES('Hello There!');
INSERT INTO messages (message) VALUES('Hola!');
INSERT INTO messages (message) VALUES('G\'day');