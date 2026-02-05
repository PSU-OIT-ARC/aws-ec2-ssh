#!/usr/bin/env python3

import sqlite3
import getpass
import time
import sys

__copyright__ = 'Copyright 2025 Jan-Piet Mens'
__license__   = """WTFPL"""


class Database:
    def __init__(self, dbname):
        try:
            self.conn = sqlite3.connect(dbname)
        except sqlite3.Error as err:
            print("sqlite error code {0}: {1}".format(err.sqlite_errorcode, err.sqlite_errorname), file=sys.stderr)
            exit(1)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
 
    def getKeys(self, username):
        sql = "SELECT updated FROM metadata WHERE username = ?"
        self.cursor.execute(sql, [getpass.getuser()])
        result = self.cursor.fetchone()
        if result is None or len(result) != 1:
            raise RuntimeError("No metadata available for user {}".format(username))

        timestamp = int(result[0])

        sql = "SELECT pubkey FROM sshkeys WHERE username = ? and updated >= ?"
        self.cursor.execute(sql, [username, timestamp - 21600])

        results = self.cursor.fetchall()
        return results
 
    def close(self):
        self.conn.commit()
        self.conn.close()


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: %s username" % (sys.argv[0]), file=sys.stderr)
        sys.exit(1)

    username = sys.argv[1]
    db = Database("/opt/authorized_keys.db")

    # get keys and print them one per line for sshd to decide which one to verify/use
    # this is where the program could decide to perform additional checks such as
    # permission to access this host, at this time, by this user, etc.

    pubkeys = db.getKeys(username)
    for r in pubkeys:
        print(r["pubkey"].rstrip())

    db.close()
