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

db_name = db_login["dbname"]
table_name = pmdr_cf["table_name"]
enum_name = pmdr_cf["enum_type"]
enum_values = pmdr_cf["enum_values"]

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

def check_type_values() -> bool:
    logger.debug(f"Checking if type ({enum_name}) has the correct values ({enum_values})")
    return cur.execute(f"SELECT enum_range(null::{enum_name});").fetchone()[0] == enum_values

# Check if the pomodoro table exist
if check_table_exist(table_name):
    logger.debug(f"Table ({table_name}) in database ({db_name}) found.")
else:
    logger.info(f"Table ({table_name}) in database ({db_name}) not found, creating table")
    # Create the table if it doesn't exist 
    try:
        cur.execute(f"CREATE TABLE {table_name} ();")
    except psycopg.errors.InsufficientPrivilege as e:
        logger.error(f"No access right to create table: {str(e).split('LINE')[0].replace("\n", "")}, check and grant access in pgAdmin and try again")
        os._exit(1)
    finally:
        logger.debug(f"Table ({table_name}) in database ({db_name}) created")
        conn.commit()
        logger.debug("Db changes committed")

# Check if enum type exist and is correct
# TODO

# # Check whether the enum type exist and create it if it doesn't exist
# if not check_type_exist():
#     logger.info(f"Type ({enum_name}) does not exist, creating type")
#     cur.execute(f"CREATE TYPE {enum_name} AS ENUM ('break', 'focus');")
# else:
#     # If enum type exist, check if it has the correct values
#     logger.debug(f"Type ({enum_name}) found.")
#     if not check_type_values():
#         # If incorrect enum values, delete type and recreate it
#         logger.info(f"Type ({enum_name}) has incorrect values ({enum_values}). Dropping and creating type")
#         cur.execute(f"DROP TYPE {enum_name}; \
#                     CREATE TYPE {enum_name} AS ENUM ('break', 'focus');")
#     else:
#         logger.debug(f"Type ({enum_name}) has the correct values ({enum_values})")

# Check if table column is correct
# TODO 

def end_connection() -> bool:
    logger.debug("Closing db cursor and db connection")
    cur.close()
    conn.close()
    return cur.closed and conn.closed 

if __name__ == "__main__":
    end_connection()
