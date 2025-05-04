import psycopg, sys
import src.overhead as oh 

# Get configurations and logger
db_config = oh.read_config()["postgres"]
logger = oh.get_logger("Todoro", mode="w")
logger.debug("Logger started")

# importing later so the logs are not overwritten 
import src.timer as tm 
import src.db as db

# TIMER 
focus_time = {"s": 25, "l": 45}
break_time = {"s": 15, "l": 45}
focus = None

# Ask if user is focusing or taking a break
focus_or_break = oh.input_check("(f)ocus or (b)reak time: ", ["f", "b"])
focus = True if focus_or_break == "f" else False
short_time = focus_time["s"] if focus else break_time["s"]
long_time = focus_time["l"] if focus else break_time["l"]

# Ask if user wants the short or long time
short_or_long_time = oh.input_check(f"(s)hort time [{short_time} mins] or (l)ong time [{long_time} mins]: ", ["s", "l"])
time = short_time if short_or_long_time == "s" else long_time 

logger.debug(f"User chose ({focus_or_break}) and ({short_or_long_time})")

# Triggering timer and add to database 
logger.debug("Triggering the timer")
if tm.timer(time):
    # Add to database for successfully completed timer (i.e. not quit)
    # TODO
    pass 

# Closing connection to postgres db
if db.end_connection():
    logger.debug("Connection and cursor to db closed")