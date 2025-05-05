import psycopg, sys, os

if __name__ == "__main__":
    import overhead as oh
else:
    import src.overhead as oh 

# Get logger and start logging
logger = oh.get_logger("db_func")
logger.debug("Logger started")

# Get db configurations
logger.debug("Getting postgres configuration from json")
cf = oh.read_config()

db_login = cf["postgres"]
pmdr_cf = cf["pomodoro"]

pmdr_cols = pmdr_cf["columns"]
db_name = db_login["dbname"]
table_name = pmdr_cf["table_name"]
enum_name = pmdr_cf["enum_type"]

# Creating cursor to db
try: 
    conn = psycopg.connect(f"user={db_login["user"]} dbname={db_name} password={db_login["pw"]}")
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
                          WHERE table_name='{tb_name}' AND table_schema='public' AND table_catalog='{db_name}')""").fetchone()[0]

def check_type_exist(enum_name: str) -> bool:
    logger.debug(f"Checking if type ({enum_name}) exists")
    return cur.execute(f"SELECT EXISTS(SELECT * FROM pg_type WHERE typname='{enum_name}')").fetchone()[0]

def get_table_columns(tb_name: str) -> set:
    logger.debug(f"Getting columns for ({table_name})")
    return set([c for c, _ in cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{tb_name}';").fetchall()])

# Check if the pomodoro table exist
if check_table_exist(table_name):
    logger.debug(f"Table ({table_name}) in database ({db_name}) found")
else:
    logger.info(f"Table ({table_name}) in database ({db_name}) not found, creating table")
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
desired_cols = sorted(set(pmdr_cols.keys()))
if cols == desired_cols:
    logger.debug(f"Columns of ({table_name}) are correct: {cols}")

else:
    logger.info(f"Columns of ({table_name}) are incorrect: {cols}, creating columns")
    # Create columns if they don't exist 
    # Loops through the set of column and check if it is in the existing columns, extra columns are ignored (not deleted)
    for col in desired_cols:
        if col not in cols:
            cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} {pmdr_cols[col]} NOT NULL")
            logger.info(f"Added column ({col}) with type ({pmdr_cols[col]})")


            if col == pmdr_cf["pkey"]:
                cur.execute(f"ALTER TABLE {table_name} ADD PRIMARY KEY ({col})")
                logger.info(f"Set column ({col}) as primary key")

logger.debug("Db changes committed")

# NOTE: values sequence are hard coded: duration, end time, start time and timer type
# Any changes to the columns name will break this 
def add_timer_row(start_time, end_time, duration:int , timer_category:str) -> None:
    cur.execute(f"INSERT INTO {table_name} (start_time, end_time, duration, timer_category) \
                VALUES ('{start_time}', '{end_time}', {duration}, '{timer_category}')")
    conn.commit()
    logger.info(f"Added entry to ({table_name}) with {start_time} START, {end_time} END, {duration} DURATION, {timer_category} TYPE")

def end_connection() -> bool:
    # Commit changes then close db cursor and db connection
    conn.commit()
    logger.debug("Closing db cursor and db connection")
    cur.close()
    conn.close()
    return cur.closed and conn.closed 

if __name__ == "__main__":
    end_connection()
