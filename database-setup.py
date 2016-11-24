import pg

db = pg.DB(dbname = "home-project-database", user = "rahul")

# Create the tables in the Database
# Create a User table
db.query("create table users(id serial primary key, name varchar(250), data varchar(1000))")

