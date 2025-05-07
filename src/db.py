import psycopg, sys, os
import overhead as oh 

# Get logger and start logging
logger = oh.get_logger("db_func")
logger.debug("Logger started")

# Get db configurations
logger.debug("Getting postgres configuration from json")
db_login = oh.read_config()["postgres"]

# NOTE: Hard coded table names, column names, enum name, and primary key
table_name = "pomodoro"
start_time = "start_time"
end_time = "end_time"
duration = "duration" 
timer_category = "timer_category"
enum_name = "timer_type"
pkey = "start_time"
task = "task"

# First element in list is the type of the column, second element indicates if NOT NULL (true = NOT NULL)
columns = {start_time: ["TIMESTAMP WITH TIME ZONE", True], end_time: ["TIMESTAMP WITH TIME ZONE", True], 
           duration: ["INT", True], timer_category: [enum_name, True], task: ["VARCHAR", False]}

# Connecting to db and creating cursor to db
try: 
    conn = psycopg.connect(f"user={db_login["user"]} dbname={db_login["dbname"]} password={db_login["pw"]}")
    logger.debug("Connected to db")
    cur = conn.cursor()
    logger.debug("Cursor to db created")

except psycopg.OperationalError as e:
    logger.error("Connection to database failed")
    logger.error(e)
    sys.exit(1)

def check_table_exist(tb_name: str) -> bool:
    logger.debug(f"Checking if table ({tb_name}) exists")
    return cur.execute(f"""SELECT EXISTS(SELECT * FROM information_schema.tables 
                          WHERE table_name='{tb_name}' AND table_schema='public' AND table_catalog='{db_login["dbname"]}')""").fetchone()[0]

def check_type_exist(enum_name: str) -> bool:
    logger.debug(f"Checking if type ({enum_name}) exists")
    return cur.execute(f"SELECT EXISTS(SELECT * FROM pg_type WHERE typname='{enum_name}')").fetchone()[0]

def get_table_columns(tb_name: str) -> set:
    logger.debug(f"Getting columns for ({table_name})")
    return set([c for c, _ in cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{tb_name}';").fetchall()])

# Check if the pomodoro table exist
if check_table_exist(table_name):
    logger.debug(f"Table ({table_name}) in database found")
else:
    logger.info(f"Table ({table_name}) in database not found, creating table")
    # Create the table if it doesn't exist 
    try:
        cur.execute(f"CREATE TABLE {table_name} ();")
    except psycopg.errors.InsufficientPrivilege as e:
        logger.error(f"No access right to create table: {str(e).split('LINE')[0].replace("\n", "")}, check and grant access in pgAdmin and try again")
        sys.exit(1)

# Check if enum type exist 
# NOTE: enum values are not checked 
if check_type_exist(enum_name):
    logger.debug(f"Type ({enum_name}) found.")

# If enum type does not exist, create it
else:
    logger.info(f"Type ({enum_name}) does not exist, creating type")
    cur.execute(f"CREATE TYPE {enum_name} AS ENUM ('break', 'focus');")

# Check if table column heading is correct
# NOTE: the type for the column is NOT checked 
cols = sorted(get_table_columns(table_name))
desired_cols = sorted(set(columns.keys()))
if cols == desired_cols:
    logger.debug(f"Columns of ({table_name}) are correct: {cols}")

else:
    logger.info(f"Columns of ({table_name}) are incorrect: {cols}, creating columns")
    # Create columns if they don't exist 
    # Loops through the set of column and check if it is in the existing columns, extra columns are ignored (not deleted)
    for col in desired_cols:
        if col not in cols:
            cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} {columns[col][0]}{ "NOT NULL"*int(columns[col][1])}")
            logger.info(f"Added column ({col}) with type ({columns[col][0]}) and NOT NULL is {columns[col][1]}")


            if col == pkey:
                cur.execute(f"ALTER TABLE {table_name} ADD PRIMARY KEY ({col})")
                logger.info(f"Set column ({col}) as primary key")

logger.debug("Db changes committed")

# NOTE: values sequence are hard coded: duration, end time, start time and timer type
# Any changes to the columns name will break this 
def add_timer_row(start_time, end_time, duration:int , timer_category:str, task="") -> None:
    cur.execute(f"INSERT INTO {table_name} (start_time, end_time, duration, timer_category, task) \
                VALUES ('{start_time}', '{end_time}', {duration}, '{timer_category}', '{task}')".replace("'None'","NULL"))
    conn.commit()
    logger.info(f"Added entry to ({table_name}) with {start_time} START, {end_time} END, {duration} DURATION, {timer_category} TYPE, {task} TASK")

def end_connection() -> bool:
    # Commit changes then close db cursor and db connection
    conn.commit()
    logger.debug("Closing db cursor and db connection")
    cur.close()
    conn.close()
    return cur.closed and conn.closed 

if __name__ == "__main__":
    end_connection()
