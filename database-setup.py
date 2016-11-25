import pg
import urlparse

url = "postgres://xfckxhvrnurzab:grWHL5-NDkLx60q3ha1sW-gvHt@ec2-174-129-3-207.compute-1.amazonaws.com:5432/dfjp7s1fia74dc"

url = urlparse.urlparse(url)
db = pg.DB(dbname = url.path[1:], host = url.hostname, port = url.port, user = url.username, passwd = url.password)

# Create the tables in the Database
# Create a User table
db.query('begin')

db.query("create table users(id serial primary key, name varchar(250), email varchar(250), picture varchar (250), data varchar(2000) DEFAULT 'DEFAULT', time varchar(30))")

db.query('end')
