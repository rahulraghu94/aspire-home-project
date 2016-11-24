import pg

db = pg.DB(dbname = "home-project-database", user = "rahul")

# Create the tables in the Database
# Create a User table
db.query('begin')

db.query("create table users(id serial primary key, name varchar(250), email varchar(250), picture varchar (250), data varchar(2000) DEFAULT 'DEFAULT', time varchar(30))")

db.query('end')
