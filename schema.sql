<<<<<<< HEAD
=======
-- DROP DATABASE IF EXISTS photoshare;
>>>>>>> 79b0a3e67243b061fd04c9d040b075548469ee27
CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;

CREATE TABLE Users(
 user_id INTEGER AUTO_INCREMENT,
 fname VARCHAR(80) NOT NULL,
 lname VARCHAR(80) NOT NULL,
 email VARCHAR(255) NOT NULL,
 gender CHAR(10),
 dob DATE NOT NULL,
 hometown VARCHAR(100),
 password VARCHAR(255) NOT NULL,
 PRIMARY KEY (user_id)
 );

CREATE TABLE Albums(
 albums_id INTEGER AUTO_INCREMENT,
 aname VARCHAR(80),
 creation_date DATE,
 user_id INTEGER NOT NULL,
 PRIMARY KEY (albums_id),
 FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Photos(
 photo_id INTEGER AUTO_INCREMENT,
 user_id INTEGER NOT NULL,
 data LONGBLOB,
 caption VARCHAR(255),
 albums_id INTEGER NOT NULL,
 PRIMARY KEY (photo_id),
 FOREIGN KEY (albums_id) REFERENCES Albums (albums_id),
 FOREIGN KEY (user_id) REFERENCES Users (user_id)
);

CREATE TABLE Tags(
 tag_id INTEGER AUTO_INCREMENT,
 word VARCHAR(100),
 PRIMARY KEY (tag_id)
);

CREATE TABLE Comments(
 comment_id INTEGER AUTO_INCREMENT,
 user_id INTEGER NOT NULL,
 photo_id INTEGER NOT NULL,
 text VARCHAR (255),
 comment_date DATE,
 PRIMARY KEY (comment_id),
 FOREIGN KEY (user_id) REFERENCES Users (user_id),
 FOREIGN KEY (photo_id) REFERENCES Photos (photo_id)
);

CREATE TABLE Likes(
 photo_id INTEGER,
 user_id INTEGER,
 PRIMARY KEY (photo_id,user_id),
 FOREIGN KEY (photo_id) REFERENCES Photos (photo_id),
 FOREIGN KEY (user_id) REFERENCES Users (user_id)
);

CREATE TABLE Tagged(
 photo_id INTEGER,
 tag_id INTEGER,
 PRIMARY KEY (photo_id, tag_id),
 FOREIGN KEY(photo_id) REFERENCES Photos (photo_id),
 FOREIGN KEY(tag_id) REFERENCES Tags (tag_id)
);

CREATE TABLE Friends(
 user_id1 INTEGER,
 user_id2 INTEGER,
 PRIMARY KEY (user_id1, user_id2),
 FOREIGN KEY (user_id1) REFERENCES Users(user_id),
 FOREIGN KEY (user_id2) REFERENCES Users(user_id),
 constraint Friendship CHECK (user_id1 <> user_id2)
);

INSERT INTO Users (user_id, email, password, fname, lname, gender, dob, hometown) 
VALUES (0,'test@bu.edu','0test0','Luna','Zhu','Female', '2000-01-01','Covina, CA');

SELECT * FROM Friends;
SELECT * FROM Users;
SELECT * FROM Albums;
SELECT * FROM Photos;
SELECT * FROM Tags;

-- DROP TABLE Tagged;
-- DROP TABLE Tags;

