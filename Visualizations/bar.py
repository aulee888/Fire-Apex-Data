import pandas as pd
import sqlite3
import matplotlib.pyplot as plt


def bar(ax, query_loc, x, y, sort_by=None):
    """
    Can remove sort_by and make it so that it sorts by var y.
    """
    conn = sqlite3.connect('apex.db')
    stmt = open(query_loc)

    df = pd.read_sql_query(stmt.read(), conn)
    
    if sort_by:
        df = df.sort_values(by=sort_by, ascending=False)

    stmt.close()
    conn.close()

    return ax.barh(df[x], df[y])


fig, (ax1, ax2) = plt.subplots(2, 1)
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=90)
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=90)
bar(ax1, 'scripts/weapon-kills.txt', 'weapon', 'kills', sort_by='kills')
bar(ax2, 'scripts/weapon-kills.txt', 'weapon', 'damage', sort_by='damage')
plt.show()

# Top weapons based on top 5 placement
# stmt = open('queries/top-weapons.txt').read()
# df = pd.read_sql_query(stmt, conn)
# plt.bar(df['weapon'], df['count'])
# plt.xticks(rotation=50)
# plt.show()


# Top weapons based on damage
# stmt = open('queries/weapon-kills.txt').read()
# df = pd.read_sql_query(stmt, conn)
# plt.bar(df['weapon'], df['damage'])
# plt.xticks(rotation=90)
# plt.show()

# Top weapons based on kills
# stmt = open('queries/weapon-kills.txt').read()
# df = pd.read_sql_query(stmt, conn)
# plt.bar(df['weapon'], df['kills'])
# plt.xticks(rotation=90)
# plt.show()
