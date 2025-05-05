import time, msvcrt, sys
from pynput.keyboard import Key, Listener 
from win32.win32gui import GetWindowText, GetForegroundWindow

if __name__ == "__main__":
    import overhead as oh
else:
    import src.overhead as oh 

# Get logger and start logging 
logger = oh.get_logger("Timer")
logger.debug("Logger started")

pause = False # Flag for pausing the timer
quit = False # Flag for quitting the timer
def release_key(k): 
    '''Function is called when any key is released'''
    # Check that key presses are in the Todoro window (has the word "Todoro"), otherwise ignore
    curr_window = GetWindowText(GetForegroundWindow()).lower()
    # logger.debug(f"Detected keypress in: ({curr_window})")
    if "todoro" not in curr_window or "visual studio" in curr_window:
        return
    
    global pause, quit
    try:
        if k == Key.space:
            logger.debug("Release of the space key detected, proceed to un/pause timer")
            pause = False if pause else True
        elif k.char == 'q':
            logger.debug("Release of the q key detected, proceed to quit timer")
            quit = True 
    except AttributeError as e:
        logger.warning(f"AttributeError detecting key press ({k}): {e}") # Some keys does not have char attribute

def timer(minute: int, second=0) -> bool:
    """Starts a timer of (mins) mins and (sec (default 0)) seconds, press space to pause and unpause, press q to quit """

    # Starts the listener object to detect key releases 
    logger.debug("Listener object started")
    listener = Listener(on_release=release_key)
    listener.start()

    logger.debug(f"Timer of {minute} m and {second} s started")
    for s in range(minute*60 + second, 0, -1):

        # If paused, keep looping until unpaused 
        while pause and not quit:
            continue

        # Update the timer on the command line
        min = s // 60
        sec = s % 60
        sys.stdout.write("\r")
        sys.stdout.write(f"{min:>2} m {sec:>2} s")
        sys.stdout.flush()

        # If q is pressed, quit the timer 
        if quit:
            sys.stdout.write("\r")
            sys.stdout.write(f"Quitting timer with {min:>2} m {sec:>2} s left")
            sys.stdout.flush()
            logger.debug(f"Quitting timer with {min:>2} m {sec:>2} s left")
            break

        time.sleep(1)

    # Clears the command line
    sys.stdout.write("\r")
    sys.stdout.write("")
    sys.stdout.flush()

    if not quit:
        print(f"{minute} m and {second} s completed")
        logger.debug(f"Timer of {minute} m and {second} s completed")
    
    listener.stop()
    logger.debug("Listener object stopped")

    # Clears the input stream so key pressed during timer is not shown 
    while msvcrt.kbhit():
        msvcrt.getch()
    return not quit

if __name__ == "__main__":
    timer(0, 15)