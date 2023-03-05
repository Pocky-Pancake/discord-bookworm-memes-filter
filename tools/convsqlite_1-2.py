import sqlite3, os

check = os.listdir("..")
exist = False
for x in check:
    if x == "bot.sqlite3":
        print("File 'bot.sqlite3' found!")
        exist = True

if exist:
    ask = True
    ans = ""
    while ask:
        ans = input("Do you wish to upgrade 'bot.sqlite3' to 'bot2.sqlite'? (y/n) ")
        if ans == "y" or ans == "Y" or ans == "n" or ans == "N":
            ask = False
    if ans == "y" or ans == "Y":
        conn_old = sqlite3.connect("../bot.sqlite3")
        c_old = conn_old.cursor()
        conn_new = sqlite3.connect("../bot2.sqlite3")
        c_new = conn_old.cursor()

        c_new.execute("""CREATE TABLE threads (
            user_id integer,
            thread_id integer,
            guild_id integer,
            embedmsg_id integer
        )""")

        c_new.execute("""CREATE TABLE channels (
            channel_id integer,
            guild_id integer,
            type integer,
            int_val1 integer,
            str_val1 text,
            str_val2 text,
            str_val3 text
        )""")
        print("Created tables")

        get_threads = c_old.execute("SELECT thread_id FROM threads").fetchall()
        for x in get_threads:
            print(f"THREAD {x[0]}")
            get_user = c_old.execute(f"SELECT user_id FROM threads WHERE thread_id = ?", [x[0]]).fetchone()
            print(f"USER {get_user[0]}")
            get_guild = c_old.execute(f"SELECT guild_id FROM threads WHERE thread_id = ?", [x[0]]).fetchone()
            print(f"GUILD {get_guild[0]}")
            get_embed = c_old.execute(f"SELECT embedmsg_id FROM threads WHERE thread_id = ?", [x[0]]).fetchone()
            print(f"EMBED {get_embed[0]}")
            sql = "INSERT INTO threads (user_id, thread_id, guild_id, embedmsg_id, state) VALUES (?, ?, ?, ?, ?)"
            val = (get_user[0], x[0], get_guild[0], get_embed[0], None)
            c_new.execute(sql,val)
            conn_new.commit()
        get_filters = c_old.execute("SELECT channel_id FROM filters").fetchall()
        for x in get_filters:
            print(f"FILTER {x[0]}")
            get_guild = c_old.execute(f"SELECT guild_id FROM filters WHERE channel_id = ?", [x[0]]).fetchone()
            print(f"GUILD {get_guild[0]}")
            get_warn = c_old.execute(f"SELECT warn_msg FROM filters WHERE channel_id = ?", [x[0]]).fetchone()
            print(f"WARN {get_warn[0]}")
            get_name = c_old.execute(f"SELECT default_thread_name FROM filters WHERE channel_id = ?", [x[0]]).fetchone()
            print(f"NAME {get_name[0]}")
            sql = "INSERT INTO channels (channel_id, guild_id, type, int_val1, str_val1, str_val2, str_val3) VALUES (?, ?, ?, ?, ?, ?, ?)"
            val = (x[0], get_guild[0], 0, None, get_warn[0], get_name[0], None)
            c_new.execute(sql,val)
            conn_new.commit()
        print("Upgrade Completed! You may delete the old 'bot.sqlite3'")
    else:
        print("Aborted")
else:
    print("File 'bot.sqlite3' not found! Aborted.")

