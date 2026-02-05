#!/usr/bin/env python3

import subprocess
import sqlite3
import getpass
import time
import sys


class Database:
    def __init__(self, dbname):
        try:
            self.conn = sqlite3.connect(dbname)
        except sqlite3.Error as err:
            print("sqlite error code {0}: {1}".format(err.sqlite_errorcode, err.sqlite_errorname), file=sys.stderr)
            exit(1)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def createDatabase(self):
        sql = "CREATE TABLE IF NOT EXISTS metadata (username VARCHAR(20) NOT NULL UNIQUE, updated INTEGER DEFAULT 0);"
        self.cursor.execute(sql)

        sql = "CREATE TABLE IF NOT EXISTS sshkeys (username VARCHAR(20) NOT NULL, pubkey VARCHAR(512) NOT NULL, updated INTEGER DEFAULT 0, CONSTRAINT unique_entry UNIQUE (username, pubkey));"
        self.cursor.execute(sql)

    def updateMetadata(self, user):
        timestamp = int(time.time())
        sql = "INSERT INTO metadata (username, updated) VALUES (?, ?) ON CONFLICT (username) DO UPDATE SET updated = ?"
        self.cursor.execute(sql, ["nobody", timestamp, timestamp])
        self.cursor.execute(sql, [user, timestamp, timestamp])

    def updateKey(self, username, pubkey):
        timestamp = int(time.time())
        sql = "INSERT INTO sshkeys (username, pubkey, updated) VALUES (?, ?, ?) ON CONFLICT (username, pubkey) DO UPDATE SET updated=?"
        self.cursor.execute(sql, [username, pubkey, timestamp, timestamp])

    def close(self):
        self.conn.commit()
        self.conn.close()


if __name__ == "__main__":

    if len(sys.argv) != 1:
        print("Usage: %s" % (sys.argv[0]), file=sys.stderr)
        sys.exit(1)

    username = getpass.getuser()
    db = Database("/opt/authorized_keys.db")

    # ensure that the local pubkey database has been created
    db.createDatabase()

    # ensure that the local pubkey database metadata is updated
    db.updateMetadata(username)

    # get registered pubkeys for all synced users and add them to the database
    user_output = subprocess.check_output(["/usr/bin/getent", "group", "iam-synced-users"], text=True)
    if user_output.split(":") and len(user_output.split(":")) == 4:
       for user in user_output.split(":")[3].split(","):
           for key in subprocess.check_output(["/opt/authorized_keys_command.sh", user.strip()], text=True).splitlines():
               db.updateKey(user, key.strip())

    db.close()
