# TIMINGS
focus_time = {"s": 1, "l": 45}
break_time = {"s": 10, "l": 30}
focus = None 

if __name__ == "__main__":

    import overhead as oh 

    # Get logger
    logger = oh.get_logger("Todoro", mode="w")
    logger.debug("Logger started")

    # importing later so the logs are not overwritten 
    import timer as tm 
    import db as db



    try: 
        while True: 
            # Ask if user is focusing or taking a break
            focus_or_break = oh.input_check("\n(f)ocus or (b)reak time: ", ["f", "b"])
            focus = True if focus_or_break == "f" else False
            short_time = focus_time["s"] if focus else break_time["s"]
            long_time = focus_time["l"] if focus else break_time["l"]

            # Ask if user wants the short or long time
            short_or_long_time = oh.input_check(f"(s)hort time [{short_time} mins] or (l)ong time [{long_time} mins]: ", ["s", "l"])
            time = short_time if short_or_long_time == "s" else long_time 

            logger.debug(f"User chose ({focus_or_break}) and ({short_or_long_time})")

            # Triggering timer and add to database 
            row_dict = {c: None for c in db.desired_cols} # Dictionary object to pass to function for adding row to db
            logger.debug("Triggering the timer")
            row_dict[db.start_time] = oh.get_datetime_now()
            if tm.timer(time):
                # Add to database for successfully completed timer (i.e. not quit)
                oh.chime.info() # Chime sound when timer ends 
                row_dict[db.end_time] = oh.get_datetime_now()
                row_dict[db.duration] = time * 60
                row_dict[db.timer_category] = "focus" if focus else "break"
                db.add_timer_row(**row_dict)

    except KeyboardInterrupt:
        # Ctrl + C to end the program 
        logger.debug("KeyInterrupt detected, ending program")
        print("\nEnding program...")

    finally:
        # Closing connection to postgres db
        if db.end_connection():
            logger.debug("Connection and cursor to db closed")