import psycopg, logging, json, sys, os
import src.timer as tm 
import src.overhead as oh 

# Get directory of file path as config.json and logs are relative to this file
curr_dir = os.path.dirname(__file__)

# Get configurations from config file
try: 
    with open(curr_dir + "\\config\\config.json") as fconfig:
        config = json.load(fconfig)
        log_config = config["logging"]
        db_config = config["postgres"]
except Exception as e:
    print("Failed to open config.json: ", e)
    sys.exit(1)


# Start logging in debug mode, outputs to both logfile and terminal 
logging.basicConfig(level=logging.DEBUG, format=log_config["format"], style="{",
                    handlers=[logging.FileHandler(curr_dir + log_config["outfile"]), logging.StreamHandler()])
logger = logging.getLogger("Todoro")
logger.debug("Logger started")

# Connect to database 
try: 
    conn = psycopg.connect(f"user={db_config["user"]} dbname={db_config["dbname"]} password={db_config["pw"]}")
    logger.debug("Connected to database")
    cur = conn.cursor()
    # TODO: Check if table exist, maybe check schema also?

except psycopg.OperationalError as e:
    logger.error("Connection to database failed")
    logger.error(e)
    sys.exit(1)

# TIMER 
focus_time = {"s": 25, "l": 45}
break_time = {"s": 15, "l": 45}
focus = None

# Ask if user is focusing or taking a break
logger.debug("Checking focus time or break time")
focus_or_break = oh.input_check("(f)ocus or (b)reak time: ", ["f", "b"])
focus = True if focus_or_break == "f" else False
short_time = focus_time["s"] if focus else break_time["s"]
long_time = focus_time["l"] if focus else break_time["l"]

# Ask if user wants the short or long time
logger.debug("Checking short time or long time")
short_or_long_time = oh.input_check(f"(s)hort time [{short_time} mins] or (l)ong time [{long_time} mins]: ", ["s", "l"])
time = short_time if short_or_long_time == "s" else long_time 

# Triggering timer and add to database 
logger.debug("Triggering the timer")
if tm.timer(time):
    # TODO: Add to database 
    pass 

# Closing connection to postgres db
logger.debug("Closing connection and cursor to db")
cur.close()
conn.close()
if cur.closed and conn.closed:
    logger.debug("Connection and cursor to db closed")