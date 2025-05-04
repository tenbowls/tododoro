# General Note
- This is a pomodoro timer with tracking using PostgreSQL database (with local server)

# PostgreSQL
- Installation of PostgreSQL on local PC is needed 
- Create a database on the SQL server with name "todoro" (if using different name, db name must match in the config file)
- Create a username and password for the db server, add the username and password to the config file, alternatively, edit the "pg_hba.conf" file to enable server to trust the username so no password needs to be supplied
- Make sure the user has permission to modify the table including the public schema
