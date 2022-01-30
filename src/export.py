#!/usr/bin/env python3

import csv
import io


def dump_csv(db):
    result = io.StringIO()
    cw = csv.writer(result)
    cw.writerow(
        ["created", "issue", "maturity", "event type", "side", "price", "quantity"]
    )
    with db.conn.cursor() as curs:
        curs.execute(
            """SELECT created, url, matures, class, side, price, quantity
                        FROM ticker ORDER BY created;
                     """
        )
        for row in curs.fetchall():
            row = list(row)
            row[0] = row[0].strftime("%x %X")
            row[2] = row[2].strftime("%x %X")
            if row[4]:
                row[4] = "FIXED"
            else:
                row[4] = "UNFIXED"
            row[5] = row[5] / 1000
            cw.writerow(row)
    return result
