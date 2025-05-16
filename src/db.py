import psycopg, sys
from enum import Enum 

if __name__ == "__main__":
    import overhead as oh 
else:
    import src.overhead as oh 

# Get logger and start logging
logger = oh.get_logger("db_func")
logger.debug("Logger started")

# Get db configurations
logger.debug("Getting postgres configuration from json")
db_login = oh.read_config()["postgres"]

# NOTE: Hard coded table names, column names, enum name, and primary key for POMODORO table
table_name = "pomodoro"
start_time = "start_time"
end_time = "end_time"
duration = "duration" 
timer_category = "timer_category"
enum_name = "timer_type"
pkey = "start_time"
task = "task"

# First element in list is the type of the column, second element indicates if NOT NULL (true = NOT NULL)
pmdr_columns = {start_time: ["TIMESTAMP WITH TIME ZONE", True], end_time: ["TIMESTAMP WITH TIME ZONE", True], 
           duration: ["INT", True], timer_category: [enum_name, True], task: ["VARCHAR", False]}

# Hard coded table names, column names for todolist section 
class Todolist(Enum):
    # Three tables for the todolist section 
    TABLE_SECTION = "todolist_section"
    TABLE_MAIN_TASKS = "todolist_main_tasks"
    TABLE_SUB_TASKS = "todolist_sub_tasks"

    # Columns in the section table 
    SECTION_NAME = "section_name"
    SECTION_ID = "section_id"
    SECTION_PKEY = SECTION_ID

    # Columns in the main tasks table
    MAIN_TASK_NAME = "main_task_name"
    MAIN_TASK_ID = "main_task_id"
    MAIN_TASK_PKEY = MAIN_TASK_ID

    # Columns in the sub tasks table 
    SUB_TASK_NAME = "sub_task_name"
    STATUS = "status"
    START_TIME = "start_time"
    END_TIME = "end_time"
    SUB_TASK_PKEY = START_TIME

    # Status enum type
    STATUS_ENUM = "status_type"
    STATUS_ENUM_TYPES = ("completed", "pending")

COL_SECTION = {Todolist.SECTION_NAME.value: ["VARCHAR", True], Todolist.SECTION_ID.value: ["INT", True]}
COL_MAIN_TASKS = {Todolist.MAIN_TASK_NAME.value: ["VARCHAR", True], Todolist.MAIN_TASK_ID.value: ["INT", True], Todolist.SECTION_ID.value: ["INT", True], 
                  Todolist.STATUS.value: [Todolist.STATUS_ENUM.value, True], Todolist.START_TIME.value: ["TIMESTAMP WITH TIME ZONE", True], 
                 Todolist.END_TIME.value: ["TIMESTAMP WITH TIME ZONE", False]}
COL_SUB_TASKS = {Todolist.SUB_TASK_NAME.value: ["VARCHAR", True], Todolist.MAIN_TASK_ID.value: ["INT", True], Todolist.SECTION_ID.value: ["INT", True],
                 Todolist.STATUS.value: [Todolist.STATUS_ENUM.value, True], Todolist.START_TIME.value: ["TIMESTAMP WITH TIME ZONE", True], 
                 Todolist.END_TIME.value: ["TIMESTAMP WITH TIME ZONE", False]}

# Connecting to db and creating cursor to db
try: 
    conn = psycopg.connect(f"user={db_login["user"]} dbname={db_login["dbname"]} password={db_login["pw"]}")
    logger.debug("Connected to db")
    cur = conn.cursor()
    logger.debug("Cursor to db created")

except psycopg.OperationalError as e:
    logger.error("Connection to database failed")
    logger.error(e)
    raise e

def check_table_exist(tb_name: str) -> bool:
    logger.debug(f"Checking if table ({tb_name}) exists")
    return cur.execute(f"""SELECT EXISTS(SELECT * FROM information_schema.tables 
                          WHERE table_name='{tb_name}' AND table_schema='public' AND table_catalog='{db_login["dbname"]}')""").fetchone()[0]

def check_type_exist(enum_name: str) -> bool:
    logger.debug(f"Checking if type ({enum_name}) exists")
    return cur.execute(f"SELECT EXISTS(SELECT * FROM pg_type WHERE typname='{enum_name}')").fetchone()[0]

def get_table_columns(tb_name: str) -> set:
    logger.debug(f"Getting columns for ({tb_name})")
    return set([c for c, _ in cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{tb_name}';").fetchall()])

###################################
#### Checking pomodoro section ####
###################################

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
        raise e 

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
desired_cols = sorted(set(pmdr_columns.keys()))
if cols == desired_cols:
    logger.debug(f"Columns of ({table_name}) are correct: {cols}")

else:
    logger.info(f"Columns of ({table_name}) are incorrect: {cols}, creating columns")
    # Create columns if they don't exist 
    # Loops through the set of column and check if it is in the existing columns, extra columns are ignored (not deleted)
    for col in desired_cols:
        if col not in cols:
            cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} {pmdr_columns[col][0]} {"NOT NULL"*int(pmdr_columns[col][1])}")
            logger.info(f"Added column ({col}) with type ({pmdr_columns[col][0]}) and NOT NULL is {pmdr_columns[col][1]}")

            if col == pkey:
                cur.execute(f"ALTER TABLE {table_name} ADD PRIMARY KEY ({col})")
                logger.info(f"Set column ({col}) as primary key")

###################################
#### Checking Todolist Section ####
###################################

if check_table_exist(Todolist.TABLE_SECTION.value):
    logger.debug(f"Table ({Todolist.TABLE_SECTION.value}) in database found")
else:
    logger.info(f"Table ({Todolist.TABLE_SECTION.value}) in database not found, creating table")
    # Create the table if it doesn't exist 
    try:
        cur.execute(f"CREATE TABLE {Todolist.TABLE_SECTION.value} ();")
    except psycopg.errors.InsufficientPrivilege as e:
        logger.error(f"No access right to create table: {str(e).split('LINE')[0].replace("\n", "")}, check and grant access in pgAdmin and try again")
        raise e

if check_table_exist(Todolist.TABLE_MAIN_TASKS.value):
    logger.debug(f"Table ({Todolist.TABLE_MAIN_TASKS.value}) in database found")
else:
    logger.info(f"Table ({Todolist.TABLE_MAIN_TASKS.value}) in database not found, creating table")
    # Create the table if it doesn't exist 
    try:
        cur.execute(f"CREATE TABLE {Todolist.TABLE_MAIN_TASKS.value} ();")
    except psycopg.errors.InsufficientPrivilege as e:
        logger.error(f"No access right to create table: {str(e).split('LINE')[0].replace("\n", "")}, check and grant access in pgAdmin and try again")
        raise e

if check_table_exist(Todolist.TABLE_SUB_TASKS.value):
    logger.debug(f"Table ({Todolist.TABLE_SUB_TASKS.value}) in database found")
else:
    logger.info(f"Table ({Todolist.TABLE_SUB_TASKS.value}) in database not found, creating table")
    # Create the table if it doesn't exist 
    try:
        cur.execute(f"CREATE TABLE {Todolist.TABLE_SUB_TASKS.value} ();")
    except psycopg.errors.InsufficientPrivilege as e:
        logger.error(f"No access right to create table: {str(e).split('LINE')[0].replace("\n", "")}, check and grant access in pgAdmin and try again")
        raise e

# Check if enum type exist 
# NOTE: enum values are not checked 
if check_type_exist(Todolist.STATUS_ENUM.value):
    logger.debug(f"Type ({Todolist.STATUS_ENUM.value}) found.")

# If enum type does not exist, create it
else:
    logger.info(f"Type ({Todolist.STATUS_ENUM.value}) does not exist, creating type")
    cur.execute(f"CREATE TYPE {Todolist.STATUS_ENUM.value} AS ENUM {Todolist.STATUS_ENUM_TYPES.value};")

# Check if table column heading for SECTION table is correct
# NOTE: the type for the column is NOT checked 
cols = sorted(get_table_columns(Todolist.TABLE_SECTION.value))
desired_cols = sorted(set(COL_SECTION.keys()))
if cols == desired_cols:
    logger.debug(f"Columns of ({Todolist.TABLE_SECTION.value}) are correct: {cols}")

else:
    logger.info(f"Columns of ({Todolist.TABLE_SECTION.value}) are incorrect: {cols}, creating columns")
    # Create columns if they don't exist 
    # Loops through the set of column and check if it is in the existing columns, extra columns are ignored (not deleted)
    for col in desired_cols:
        if col not in cols:
            if col == Todolist.SECTION_PKEY.value:
                cur.execute(f"ALTER TABLE {Todolist.TABLE_SECTION.value} ADD COLUMN {Todolist.SECTION_PKEY.value} \
                            INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY")
                logger.info(f"Add column ({col}) and set as primary key")
            else:
                cur.execute(f"ALTER TABLE {Todolist.TABLE_SECTION.value} ADD COLUMN {col} {COL_SECTION[col][0]} {"NOT NULL"*int(COL_SECTION[col][1])}")
                logger.info(f"Added column ({col}) with type ({COL_SECTION[col][0]}) and NOT NULL is {COL_SECTION[col][1]}")
    
# Check if table column heading for MAIN TASK table is correct 
cols = sorted(get_table_columns(Todolist.TABLE_MAIN_TASKS.value))
desired_cols = sorted(set(COL_MAIN_TASKS.keys()))
if cols == desired_cols:
    logger.debug(f"Columns of ({Todolist.TABLE_MAIN_TASKS.value}) are correct: {cols}")

else:
    logger.info(f"Columns of ({Todolist.TABLE_MAIN_TASKS.value}) are incorrect: {cols}, creating columns")
    # Create columns if they don't exist 
    # Loops through the set of column and check if it is in the existing columns, extra columns are ignored (not deleted)
    for col in desired_cols:
        if col not in cols:
            if col == Todolist.MAIN_TASK_PKEY.value:
                cur.execute(f"ALTER TABLE {Todolist.TABLE_MAIN_TASKS.value} ADD COLUMN {Todolist.MAIN_TASK_PKEY.value} \
                            INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY")
                logger.info(f"Add column ({col}) and set as primary key")

            else:
                cur.execute(f"ALTER TABLE {Todolist.TABLE_MAIN_TASKS.value} ADD COLUMN {col} {COL_MAIN_TASKS[col][0]} {"NOT NULL"*int(COL_MAIN_TASKS[col][1])}")
                logger.info(f"Added column ({col}) with type ({COL_MAIN_TASKS[col][0]}) and NOT NULL is {COL_MAIN_TASKS[col][1]}")


# Check if table column heading for SUB TASK table is correct 
cols = sorted(get_table_columns(Todolist.TABLE_SUB_TASKS.value))
desired_cols = sorted(set(COL_SUB_TASKS.keys()))
if cols == desired_cols:
    logger.debug(f"Columns of ({Todolist.TABLE_SUB_TASKS.value}) are correct: {cols}")

else:
    logger.info(f"Columns of ({Todolist.TABLE_SUB_TASKS.value}) are incorrect: {cols}, creating columns")
    # Create columns if they don't exist 
    # Loops through the set of column and check if it is in the existing columns, extra columns are ignored (not deleted)
    for col in desired_cols:
        if col not in cols:
            cur.execute(f"ALTER TABLE {Todolist.TABLE_SUB_TASKS.value} ADD COLUMN {col} {COL_SUB_TASKS[col][0]} {"NOT NULL"*int(COL_SUB_TASKS[col][1])}")
            logger.info(f"Added column ({col}) with type ({COL_SUB_TASKS[col][0]}) and NOT NULL is {COL_SUB_TASKS[col][1]}")

            if col == Todolist.SUB_TASK_PKEY.value:
                cur.execute(f"ALTER TABLE {Todolist.TABLE_SUB_TASKS.value} ADD PRIMARY KEY ({Todolist.SUB_TASK_PKEY.value})")
                logger.info(f"Set column ({col}) as primary key")

conn.commit()  # Commit any changes
logger.debug("Db changes committed")

# NOTE: values sequence are hard coded: duration, end time, start time and timer type
# Any changes to the columns name will break this 
def add_timer_row(start_time: str, end_time: str, duration:int , timer_category:str, task:str) -> None:
    try:
        cur.execute(f"INSERT INTO {table_name} (start_time, end_time, duration, timer_category, task) \
                    VALUES ('{start_time}', '{end_time}', {duration}, '{timer_category}', '{task}')".replace("'None'","NULL"))
        conn.commit()
        logger.info(f"Added entry to ({table_name}) with {start_time} START, {end_time} END, {duration} DURATION, {timer_category} TYPE, {task} TASK")
    except Exception as e:
        logger.error(f"Failed to add entry to ({table_name}): {e}")
        raise e

# Class for all section/tabs related functions 
class SectionTools():
    def get_section_name() -> list:
        '''Return a list of all the section names from the todolist_section table'''
        try:
            section_name = [c[0] for c in cur.execute(f"SELECT {Todolist.SECTION_NAME.value}, {Todolist.SECTION_ID.value} \
                                                      FROM {Todolist.TABLE_SECTION.value} ORDER BY {Todolist.SECTION_ID.value};").fetchall()]
            logger.debug(f"Getting section name from '{Todolist.TABLE_SECTION.value}'")
            return section_name
        except Exception as e:
            logger.error(f"Failed to get section information from the section table ({Todolist.TABLE_SECTION.value}): {e}")
            raise e

    def add_section_name(section: str) -> None:
        '''Add a single entry to the todolist_section table of a new section_name'''
        try:
            cur.execute(f"INSERT INTO {Todolist.TABLE_SECTION.value} ({Todolist.SECTION_NAME.value}) VALUES ('{section}')")
            conn.commit()
            logger.debug(f"Adding section name '{section}' to '{Todolist.TABLE_SECTION.value}'")
        except Exception as e:
            logger.error(f"Faield to add {section} to table ({Todolist.TABLE_SECTION.value}): {e}")
            raise e
        
    def change_section_name(oldname: str, newname: str) -> None:
        '''Change the section name in the todolist_section table'''
        try:
            cur.execute(f"UPDATE {Todolist.TABLE_SECTION.value} SET {Todolist.SECTION_NAME.value} = '{newname}' \
                        WHERE {Todolist.SECTION_ID.value} = (SELECT {Todolist.SECTION_ID.value} FROM {Todolist.TABLE_SECTION.value} \
                        WHERE {Todolist.SECTION_NAME.value} = '{oldname}')")
            conn.commit()
            logger.debug(f"Updating section name from '{oldname}' to '{newname}' in '{Todolist.TABLE_SECTION.value}'")
        except Exception as e:
            logger.error(f"Failed to update {oldname} with {newname} in {Todolist.TABLE_SECTION.value}: {e}")
            raise e
    
    def delete_section_name(name: str) -> None:
        '''Delete a single row in the todolist_section based on the name'''
        try:
            cur.execute(f"DELETE FROM {Todolist.TABLE_SECTION.value} WHERE {Todolist.SECTION_NAME.value} = '{name}'")
            conn.commit()
            logger.debug(f"Deleting section '{name}' from {Todolist.TABLE_SECTION.value}")
        except Exception as e:
            logger.error(f"Failed to delete {name} from {Todolist.TABLE_SECTION.value}: {e}")
            raise e
        
    def get_section_id(name: str) -> int:
        '''Return the primary key of the section name in the todolist_section table'''
        try:
            id = cur.execute(f"SELECT {Todolist.SECTION_ID.value} FROM {Todolist.TABLE_SECTION.value} \
                             WHERE {Todolist.SECTION_NAME.value} = '{name}'").fetchone()[0]
            logger.debug(f"Got id of section {name} with id {id}")
            return id
        except Exception as e:
            logger.error(f"Failed to get section id of {name} from {Todolist.TABLE_SECTION.value}: {e}")
            raise e

# Class for all main task table related functions 
class MainTaskTools():
    def get_main_tasks() -> list:
        '''Return a list of (main_tasks, section_name)'''
        try:
            main_tasks = cur.execute(f"SELECT {Todolist.MAIN_TASK_NAME.value}, {Todolist.SECTION_NAME.value} FROM {Todolist.TABLE_SECTION.value}, \
                        {Todolist.TABLE_MAIN_TASKS.value} WHERE {Todolist.TABLE_MAIN_TASKS.value}.{Todolist.SECTION_ID.value} \
                        = {Todolist.TABLE_SECTION.value}.{Todolist.SECTION_ID.value} AND {Todolist.STATUS.value} = '{Todolist.STATUS_ENUM_TYPES.value[1]}' \
                        ORDER BY {Todolist.START_TIME.value}").fetchall()
            logger.debug(f"Getting main task details from ({Todolist.TABLE_MAIN_TASKS.value}) and ({Todolist.TABLE_SECTION.value})")
            return main_tasks
        except Exception as e:
            logger.error(f"Failed to get main task details from ({Todolist.TABLE_MAIN_TASKS.value}) and ({Todolist.TABLE_SECTION.value}): {e}")
            raise e

    def add_main_tasks(task: str, section: str) -> None:
        '''Add a single entry to the todolist_main_tasks table of a new pending main task'''
        try:
            cur.execute(f"INSERT INTO {Todolist.TABLE_MAIN_TASKS.value} ({Todolist.MAIN_TASK_NAME.value}, {Todolist.SECTION_ID.value}, \
                        {Todolist.STATUS.value}, {Todolist.START_TIME.value}) VALUES ('{task}', (SELECT {Todolist.SECTION_ID.value} FROM \
                        {Todolist.TABLE_SECTION.value} WHERE {Todolist.SECTION_NAME.value} = '{section}'), '{Todolist.STATUS_ENUM_TYPES.value[1]}', \
                        '{oh.get_datetime_now()}')")
            conn.commit()
            logger.debug(f"Adding section name '{section}' to '{Todolist.TABLE_SECTION.value}'")
        except Exception as e:
            logger.error(f"Faield to add {section} to table ({Todolist.TABLE_SECTION.value}): {e}")
            raise e

    def rename_main_tasks(oldtaskname: str, newtaskname: str, section: str) -> None:
        '''Rename the main task, function has to take note that different main task name can exist in different sections'''
        try:
            cur.execute(f"UPDATE {Todolist.TABLE_MAIN_TASKS.value} SET {Todolist.MAIN_TASK_NAME.value} = '{newtaskname}' \
                        WHERE {Todolist.MAIN_TASK_ID.value} = (SELECT {Todolist.MAIN_TASK_ID.value} FROM {Todolist.TABLE_MAIN_TASKS.value} \
                        WHERE {Todolist.MAIN_TASK_NAME.value} = '{oldtaskname}') AND {Todolist.SECTION_ID.value} = \
                        (SELECT {Todolist.SECTION_ID.value} FROM {Todolist.TABLE_SECTION.value} WHERE {Todolist.SECTION_NAME.value} = '{section}')")
            conn.commit()
            logger.debug(f"Updating main task name from '{oldtaskname}' to '{newtaskname}' in section '{section}' \
                         in table '{Todolist.TABLE_MAIN_TASKS.value}'")
        except Exception as e:
            logger.error(f"Failed to update {oldtaskname} with {newtaskname} in section {section} in table {Todolist.TABLE_MAIN_TASKS.value}: {e}")
            raise e

    def delete_main_tasks(task: str, section: str) -> None:
        '''Delete a single row based on the main task name and the section name'''
        try:
            cur.execute(f"DELETE FROM {Todolist.TABLE_MAIN_TASKS.value} WHERE {Todolist.MAIN_TASK_NAME.value} = '{task}' AND \
                        {Todolist.SECTION_ID.value} = (SELECT {Todolist.SECTION_ID.value} FROM {Todolist.TABLE_SECTION.value} \
                        WHERE {Todolist.SECTION_NAME.value} = '{section}') AND {Todolist.STATUS.value} = '{Todolist.STATUS_ENUM_TYPES.value[1]}'")
            conn.commit()
            logger.debug(f"Deleting main task '{task}' in section '{section}' from {Todolist.TABLE_MAIN_TASKS.value}")
        except Exception as e:
            logger.error(f"Failed to delete '{task}' from section '{section}' in table {Todolist.TABLE_MAIN_TASKS.value}: {e}")
            raise e

    def complete_main_tasks(task: str, section: str) -> None:
        '''Update the main task as completed and adds the end time'''
        try:
            cur.execute(f"UPDATE {Todolist.TABLE_MAIN_TASKS.value} SET {Todolist.STATUS.value} = '{Todolist.STATUS_ENUM_TYPES.value[0]}', \
                        {Todolist.END_TIME.value} = '{oh.get_datetime_now()}' \
                        WHERE {Todolist.MAIN_TASK_NAME.value} = '{task}' AND {Todolist.SECTION_ID.value} = \
                        (SELECT {Todolist.SECTION_ID.value} FROM {Todolist.TABLE_SECTION.value} WHERE {Todolist.SECTION_NAME.value} = '{section}')")
            conn.commit()
            logger.debug(f"Updating main task '{task}' to as completed in '{Todolist.TABLE_MAIN_TASKS.value}'")
        except Exception as e:
            logger.error(f"Failed to update {task} as completed in {Todolist.TABLE_MAIN_TASKS.value}: {e}")
            raise e
        
    def get_main_task_id(task: str, section: str) -> int:
        '''Return the main task id from main task name and section name'''
        try:
            id = cur.execute(f"SELECT {Todolist.MAIN_TASK_ID.value} FROM {Todolist.TABLE_MAIN_TASKS.value}, {Todolist.TABLE_SECTION.value} \
                            WHERE {Todolist.TABLE_MAIN_TASKS.value}.{Todolist.SECTION_ID.value} = {Todolist.TABLE_SECTION.value}.{Todolist.SECTION_ID.value} \
                            AND {Todolist.TABLE_MAIN_TASKS.value}.{Todolist.MAIN_TASK_NAME.value} = '{task}' \
                            AND {Todolist.TABLE_MAIN_TASKS.value}.{Todolist.STATUS.value} = '{Todolist.STATUS_ENUM_TYPES.value[1]}' \
                            AND {Todolist.TABLE_SECTION.value}.{Todolist.SECTION_NAME.value} = '{section}'").fetchone()[0]
            logger.debug("Got main task ({task}) from section ({section}) with main task id of {id}")
            return id
        except Exception as e:
            logger.error(f"Failed to get main task id of {task} from section {section}: {e}")
            raise e 
        
    def set_main_task_as_pending(task: str, section: str):
        try:
            cur.execute(f"UPDATE {Todolist.TABLE_MAIN_TASKS.value} SET {Todolist.STATUS.value} = '{Todolist.STATUS_ENUM_TYPES.value[1]}', \
                        {Todolist.END_TIME.value} = NULL WHERE {Todolist.MAIN_TASK_NAME.value} = '{task}' AND {Todolist.SECTION_ID.value} = \
                        (SELECT {Todolist.SECTION_ID.value} FROM {Todolist.TABLE_SECTION.value} WHERE {Todolist.SECTION_NAME.value} = '{section}')")
            conn.commit()
            logger.debug(f"Change main task {task} in section {section} to pending and clearing end time")
        except Exception as e:
            logger.error(f"Failed to set main task {task} as pending and clear end time: {e}")
            raise e

# Class for all sub task table related functions     
class SubTaskTools():
    def get_sub_tasks(main_task_id: int) -> list:
        '''Get all sub tasks with main_task_id as the parent task where sub task is not completed'''
        try:
            sub_tasks = [c[0] for c in cur.execute(f"SELECT {Todolist.SUB_TASK_NAME.value} FROM {Todolist.TABLE_SUB_TASKS.value} \
                                    WHERE {Todolist.MAIN_TASK_ID.value} = {main_task_id} \
                                    AND {Todolist.STATUS.value} = '{Todolist.STATUS_ENUM_TYPES.value[1]}' ORDER BY {Todolist.START_TIME.value}").fetchall()]
            logger.debug(f"Got sub_tasks with main_task_id ({main_task_id}): {sub_tasks}")
            return sub_tasks
        except Exception as e:
            logger.error(f"Failed to get sub tasks with main_task_id of {main_task_id}: {e}")
            raise e

    def add_sub_tasks(sub_task: str, main_task: str, section: str):
        '''Add a single entry to the todolist_sub_tasks table of a new pending sub task'''
        try:
            sectionid = SectionTools.get_section_id(section)
            maintaskid = MainTaskTools.get_main_task_id(main_task, section)
            cur.execute(f"INSERT INTO {Todolist.TABLE_SUB_TASKS.value} ({Todolist.SUB_TASK_NAME.value}, {Todolist.MAIN_TASK_ID.value}, {Todolist.SECTION_ID.value}, \
                        {Todolist.STATUS.value}, {Todolist.START_TIME.value}) VALUES ('{sub_task}', {maintaskid}, {sectionid}, '{Todolist.STATUS_ENUM_TYPES.value[1]}', \
                        '{oh.get_datetime_now()}')")
            conn.commit()
            logger.debug(f"Adding section name '{section}' to '{Todolist.TABLE_SECTION.value}'")
        except Exception as e:
            logger.error(f"Faield to add {section} to table ({Todolist.TABLE_SECTION.value}): {e}")
            raise e

    def rename_sub_tasks(old_sub_task, new_sub_task: str, main_task: str, section: str):
        '''Rename the sub task'''
        try:
            maintaskid = MainTaskTools.get_main_task_id(main_task, section)
            sectionid = SectionTools.get_section_id(section)
            cur.execute(f"UPDATE {Todolist.TABLE_SUB_TASKS.value} SET {Todolist.SUB_TASK_NAME.value} = '{new_sub_task}' \
                        WHERE {Todolist.SUB_TASK_NAME.value} = '{old_sub_task}' \
                        AND {Todolist.MAIN_TASK_ID.value} = {maintaskid} AND {Todolist.SECTION_ID.value} = {sectionid};")
            conn.commit()
            logger.debug(f"Renaming sub task {old_sub_task} of {main_task} of {section} from {Todolist.TABLE_SUB_TASKS.value} to new name '{new_sub_task}'")
        except Exception as e:
            logger.error(f"Failed to rename sub task {old_sub_task} of \
                         main task {main_task} of section {section} from {Todolist.TABLE_SUB_TASKS.value} to new name '{new_sub_task}': {e}")
            raise e


    def delete_sub_tasks(sub_task: str, main_task: str, section: str):
        '''Delete the sub task from table'''
        try:
            maintaskid = MainTaskTools.get_main_task_id(main_task, section)
            sectionid = SectionTools.get_section_id(section)
            cur.execute(f"DELETE FROM {Todolist.TABLE_SUB_TASKS.value} WHERE {Todolist.SUB_TASK_NAME.value} = '{sub_task}' \
                        AND {Todolist.MAIN_TASK_ID.value} = {maintaskid} AND {Todolist.SECTION_ID.value} = {sectionid} \
                        AND {Todolist.STATUS.value} = '{Todolist.STATUS_ENUM_TYPES.value[1]};")
            conn.commit()
            logger.debug(f"Deleting sub task {sub_task} of {main_task} of {section} from {Todolist.TABLE_SUB_TASKS.value}")
        except Exception as e:
            logger.error(f"Failed to delete sub task {sub_task} of {main_task} of {section} from {Todolist.TABLE_SUB_TASKS.value}: {e}")
            raise e

    def complete_sub_tasks(sub_task: str, main_task: str, section: str):
        '''Mark the sub task as completed and adds the end time'''
        try:
            maintaskid = MainTaskTools.get_main_task_id(main_task, section)
            sectionid = SectionTools.get_section_id(section)
            cur.execute(f"UPDATE {Todolist.TABLE_SUB_TASKS.value} SET {Todolist.STATUS.value} = '{Todolist.STATUS_ENUM_TYPES.value[0]}', \
                        {Todolist.END_TIME.value} = '{oh.get_datetime_now()}' \
                        WHERE {Todolist.SUB_TASK_NAME.value} = '{sub_task}' \
                        AND {Todolist.MAIN_TASK_ID.value} = {maintaskid} AND {Todolist.SECTION_ID.value} = {sectionid};")
            conn.commit()
            logger.debug(f"Updating {sub_task} as completed, main task id: {maintaskid}, section id: {sectionid}")
        except Exception as e:
            logger.error(f"Failed to update sub task {sub_task} as completed, main task id: {maintaskid}, section id: {sectionid}: {e}")
            raise e
        
    def set_sub_task_as_pending(sub_task: str, main_task: str, section: str):
        try:
            maintaskid = MainTaskTools.get_main_task_id(main_task, section)
            sectionid = SectionTools.get_section_id(section)
            cur.execute(f"UPDATE {Todolist.TABLE_SUB_TASKS.value} SET {Todolist.STATUS.value} = '{Todolist.STATUS_ENUM_TYPES.value[1]}', \
                        {Todolist.END_TIME.value} = NULL \
                        WHERE {Todolist.SUB_TASK_NAME.value} = '{sub_task}' \
                        AND {Todolist.MAIN_TASK_ID.value} = {maintaskid} AND {Todolist.SECTION_ID.value} = {sectionid};")
            conn.commit()
            logger.debug(f"Changed sub task {task} to pending and clearing end time")
        except Exception as e:
            logger.error(f"Failed to update sub task {sub_task} as pending in main task id: {maintaskid}, section id: {sectionid}: {e}")
            raise e

def end_connection() -> bool:
    # Commit changes then close db cursor and db connection
    conn.commit()
    logger.debug("Closing db cursor and db connection")
    cur.close()
    conn.close()
    return cur.closed and conn.closed 

if __name__ == "__main__":
    end_connection()
