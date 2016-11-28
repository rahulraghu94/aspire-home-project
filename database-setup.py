import pg
import urlparse

url = "postgres://xvnjvdhwrsvlan:eGr8AHTCTfk7NSXVp8WBegtEPK@ec2-107-22-251-151.compute-1.amazonaws.com:5432/dfgobb6m9n4ohk"

url = urlparse.urlparse(url)
db = pg.DB(dbname = url.path[1:], host = url.hostname, port = url.port, user = url.username, passwd = url.password)

default = "This is a test user string profile. You may choose to update this content by clicking the edit button. Remeber that the limit of this text field has been set to 2000, and can be changed on demand. Thi content is also borderline trivial and is present simply to fill up space, because one word text data does not look good. Hope you are having a good day!"

# Create the tables in the Database
# Create a User table
db.query('begin')

db.query("create table users(id serial primary key, name varchar(250), email varchar(250), picture varchar (250), data varchar(2000) DEFAULT 'This is a test user string profile. You may choose to update this content by clicking the edit button. Remeber that the limit of this text field has been set to 2000, and can be changed on demand. Thi content is also borderline trivial and is present simply to fill up space, because one word text data does not look good. Hope you are having a good day!', time varchar(30))")

db.query('end')
