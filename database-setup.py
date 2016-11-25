import pg
import urlparse

db = pg.DB(dbname = "home-project-database", user = "rahul")
url = "postgres://tmgaiavknsbiqy:e1NU-gRRZmXfhaIJBDDh44i5jj@ec2-50-17-206-164.compute-1.amazonaws.com:5432/d66fdt9p0ffb0u"

url = urlparse.urlparse(url)
db = pg.DB(dbname = url.path[1:], host = url.hostname, port = url.port, user = url.username, passwd = url.password)

# Create the tables in the Database
# Create a User table
db.query('begin')

db.query("create table users(id serial primary key, name varchar(250), email varchar(250), picture varchar (250), data varchar(2000) DEFAULT 'DEFAULT', time varchar(30))")

db.query('end')
