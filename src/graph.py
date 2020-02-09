#!/usr/bin/env python3

import altair as alt
import pandas as pd
import io

class Graph:
    db = None

    def __init__(self, issue=None):
        self.events = []
        all_issues = False
        if issue:
            issue = int(issue)
        else:
            all_issues = True
        with self.db.conn.cursor() as curs:
            curs.execute('''SELECT created, url, matures, class, side, price, quantity, issue
                            FROM ticker WHERE (issue = %s OR %s)
                            AND (class = 'contract_created' OR class = 'contract_resolved')
                            ORDER BY created;
                         ''', (issue, all_issues))
            for row in curs.fetchall():
                self.events.append(list(row))


    def as_html(self, height, width):
        result = io.StringIO()
        (date, etype, price, quantity, matures, issue, href, total_price) = ([], [], [], [], [], [], [], [])
        for event in self.events:
            date.append(event[0])
            etype.append(event[3])
            price.append(event[5] * 0.001)
            matures.append(event[2])
            quantity.append(event[6])
            issue.append(event[1].split('/')[-1])
            href.append('/issue/%d' % event[7])
            total_price.append(event[5] * 0.001 * event[6])

        data = pd.DataFrame({'date': date,
                             'etype': etype,
                             'price': price,
                             'matures': matures,
                             'quantity': quantity,
                             'issue': issue,
                             'href': href,
                             'total price': total_price
                            })
        chart = alt.Chart(data=data,
                          height=height,
                          width=width).mark_point().encode(x='date', y='price',
                                                           href='href:N',
                                                           tooltip=['issue', 'matures', 'price', 'quantity', 'date'])


        #chart = alt.Chart(data=data,
        #                  height=height,
        #                  width=width).mark_line().encode(x='date', y='potential worker earnings',
        #                                                  href='href:N',
        #                                                  tooltip=['issue', 'matures', 'price', 'quantity', 'date'])

        chart.save(result, format='html')
        return result.getvalue()
