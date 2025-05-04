import json, logging, sys, os

parent_dir = os.path.dirname(os.path.dirname(__file__)) # Get the parent directory of the current file path

def input_check(msg: str, v: list) -> None:
    '''Checks that user input is valid (i.e. is part of the list provided) otherwise prompts the user again'''
    ans = input(msg)
    while ans not in v:
        ans = input(msg)
    return ans 

def read_config() -> dict:
    '''Read the config.json file and return contents as a dictionary'''
    try: 
        with open(parent_dir + "\\config\\config.json") as fconfig:
            config = json.load(fconfig)
            return config
    except Exception as e:
        print("Failed to open config.json: ", e)
        sys.exit(1)

def get_logger(name: str, mode='a') -> logging.Logger:
    '''Return a logger object with the name (name), with default mode of "a" (append)'''
    config = read_config()["logging"]
    logging.basicConfig(level=logging.DEBUG, format=config["format"], style="{", filename=parent_dir + config["outfile"], filemode=mode)
    return logging.getLogger(name)