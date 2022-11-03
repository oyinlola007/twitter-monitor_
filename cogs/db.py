import sqlite3, time
from datetime import datetime

import cogs.config as config

conn = sqlite3.connect(config.DATABASE_NAME)

def initializeDB():
    try:
        conn.execute('''CREATE TABLE FOLLOWING
                 (MONITORED_ID TEXT NOT NULL,
                 SCREEN_NAME TEXT NOT NULL,
                 FOLLOWING_ID TEXT NOT NULL,
                 TIME_ADDED TEXT,
                 STATUS TEXT,
                 PRIMARY KEY (MONITORED_ID, FOLLOWING_ID));''')
    except:
        pass

    try:
        conn.execute('''CREATE TABLE MONITORING
                 (MONITORED_ID TEXT PRIMARY KEY NOT NULL,
                 SCREEN_NAME,
                 STATUS TEXT);''')
    except:
        pass

    try:
        conn.execute('''CREATE TABLE COMMANDS
                 (DESC TEXT PRIMARY KEY NOT NULL,
                 COMMAND TEXT);''')
    except:
        pass

    try:
        conn.execute('''CREATE TABLE PENDING
                 (SCREEN_NAME TEXT PRIMARY KEY NOT NULL,
                 DISCORD_ID TEXT);''')
    except:
        pass

    insert_commands("adduser", "!adduser")
    insert_commands("removeuser", "!removeuser")
    insert_commands("search", "!search")
    insert_commands("getusers", "!getusers")


def insert_following(MONITORED_ID, SCREEN_NAME, FOLLOWING_ID, COUNT_MONITOR):
    try:
        sqlite_insert_with_param = """INSERT INTO 'FOLLOWING'
                ('MONITORED_ID', 'SCREEN_NAME', 'FOLLOWING_ID', 'TIME_ADDED', 'STATUS')
                VALUES (?, ?, ?, ?, ?);"""

        #time_stamp = (datetime.now()).strftime(config.DATE_FORMAT)
        if COUNT_MONITOR == 0:
            time_stamp = int(time.time()) - 30*24*60*60
        else:
            time_stamp = int(time.time())
        data_tuple = (MONITORED_ID, SCREEN_NAME, str(FOLLOWING_ID), str(time_stamp), "1")
        conn.execute(sqlite_insert_with_param, data_tuple)
        conn.commit()
    except:
        update_following_id(MONITORED_ID, FOLLOWING_ID, "1")
        conn.commit()

def update_following_id(MONITORED_ID, FOLLOWING_ID, STATUS):
    conn.execute(f"UPDATE FOLLOWING set STATUS = '{STATUS}' where MONITORED_ID='{MONITORED_ID}' AND FOLLOWING_ID='{FOLLOWING_ID}'")
    conn.commit()

def update_followings_id(MONITORED_ID, STATUS):
    conn.execute(f"UPDATE FOLLOWING set STATUS = '{STATUS}' where MONITORED_ID='{MONITORED_ID}'")
    conn.commit()

def update_unfollowed_id(MONITORED_ID, STATUS):
    conn.execute(f"UPDATE FOLLOWING set STATUS = '{STATUS}' where MONITORED_ID='{MONITORED_ID}' AND STATUS='2'")
    conn.commit()

def update_untracked_id(MONITORED_ID, STATUS):
    conn.execute(f"UPDATE FOLLOWING set STATUS = '{STATUS}' where MONITORED_ID='{MONITORED_ID}'")
    conn.commit()

def insert_commands(DESC, COMMAND):
    try:
        sqlite_insert_with_param = """INSERT INTO 'COMMANDS'
                ('DESC', 'COMMAND')
                VALUES (?, ?);"""

        data_tuple = (DESC, COMMAND)
        conn.execute(sqlite_insert_with_param, data_tuple)
        conn.commit()
    except:
        pass

def insert_pending(SCREEN_NAME, DISCORD_ID):
    try:
        sqlite_insert_with_param = """INSERT INTO 'PENDING'
                ('SCREEN_NAME', 'DISCORD_ID')
                VALUES (?, ?);"""

        data_tuple = (SCREEN_NAME, DISCORD_ID)
        conn.execute(sqlite_insert_with_param, data_tuple)
        conn.commit()
    except:
        pass

def get_all_pending():
    return conn.execute(f"SELECT * from PENDING")

def delete_pending(SCREEN_NAME):
    conn.execute(f"DELETE from PENDING where SCREEN_NAME='{SCREEN_NAME}'")
    conn.commit()

def get_command(DESC):
    return conn.execute(f"SELECT COMMAND from COMMANDS  where DESC='{DESC}'").fetchone()[0]

def get_monitoring_status(MONITORED_ID, FOLLOWING_ID):
    return conn.execute(f"SELECT STATUS from FOLLOWING  where MONITORED_ID='{MONITORED_ID}' AND FOLLOWING_ID='{FOLLOWING_ID}'").fetchone()[0]

def insert_monitoring(MONITORED_ID, SCREEN_NAME):
    sqlite_insert_with_param = """INSERT INTO 'MONITORING'
                ('MONITORED_ID', 'SCREEN_NAME', 'STATUS')
                VALUES (?, ?, ?);"""

    data_tuple = (str(MONITORED_ID), SCREEN_NAME, "1")
    conn.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()

def update_monitoring(SCREEN_NAME, STATUS):
    conn.execute(f"UPDATE MONITORING set STATUS = '{STATUS}' where LOWER(SCREEN_NAME)='{SCREEN_NAME.lower()}'")
    conn.commit()

def count_monitor(SCREEN_NAME):
    return conn.execute(f"SELECT COUNT(SCREEN_NAME) from MONITORING where LOWER(SCREEN_NAME)='{SCREEN_NAME.lower()}'").fetchone()[0]

def count_monitor_by_id(MONITORED_ID):
    return conn.execute(f"SELECT COUNT(MONITORED_ID) from FOLLOWING where MONITORED_ID='{MONITORED_ID}'").fetchone()[0]

def get_all_monitoring():
    return conn.execute(f"SELECT * from MONITORING WHERE STATUS!='0'")

def get_latest_by_time(elapsed):
    return conn.execute(f"SELECT * from FOLLOWING where CAST(TIME_ADDED AS INT)>'{elapsed}' AND STATUS!='0' ORDER BY MONITORED_ID DESC")

def get_user_latest_by_time(elapsed, MONITORED_ID):
    return conn.execute(f"SELECT * from FOLLOWING where CAST(TIME_ADDED AS INT)>'{elapsed}' AND STATUS!='0' AND MONITORED_ID='{MONITORED_ID}'")

def get_screen_name(MONITORED_ID):
    return conn.execute(f"SELECT SCREEN_NAME from MONITORING where MONITORED_ID='{MONITORED_ID}'").fetchone()[0]

def get_monitoring_id(SCREEN_NAME):
    return conn.execute(f"SELECT MONITORED_ID from MONITORING where SCREEN_NAME='{SCREEN_NAME}' AND STATUS != '0'").fetchone()[0]



