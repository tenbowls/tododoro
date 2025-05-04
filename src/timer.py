import logging, os, json, sys, time

# Get directory of file path as config.json and logs are relative to this file
parent_dir = os.path.dirname(os.path.dirname(__file__))

# Get logging configurations
try: 
    with open(parent_dir + "\\config\\config.json") as fconfig:
        config = json.load(fconfig)
        log_config = config["logging"]
except Exception as e:
    print("Failed to open config.json: ", e)
    sys.exit(1)

# Start logging 
logging.basicConfig(level=logging.DEBUG, format=log_config["format"], style="{", 
                    handlers=[logging.FileHandler(parent_dir + log_config["outfile"]), logging.StreamHandler()])
logger = logging.getLogger("Timer")
logger.debug("Logger started")

# Timer function that prints to the terminal 
def timer(minute: int, second=0) -> bool:
    """Starts a timer of (mins) mins and (sec (default 0)) seconds"""
    logger.debug(f"Timer of {minute} m and {second} s started.")
    for s in range(minute*60 + second, 0, -1):
        min = s // 60
        sec = s % 60
        sys.stdout.write("\r")
        sys.stdout.write(f"{min:>2} m {sec:>2} s")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r")
    sys.stdout.flush()
    print(f"{minute} m and {second} s completed.")
    logger.debug(f"Timer of {minute} m and {second} s completed.")
    return True

if __name__ == "__main__":
    timer(10)