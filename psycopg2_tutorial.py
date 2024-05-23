import psycopg2
import pickle
import numpy as np

conn = psycopg2.connect(host='localhost', dbname='postgres', user='postgres', password='axionsrock', port=5432)

cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS na_scans(
            id INT PRIMARY KEY,
            f BYTEA,
            S11 BYTEA
);
            """)


id = 1
f = np.asarray([1.31, 1.32, 1.33])
S11 = np.asarray([21, 19, 22])


cur.execute("""INSERT INTO na_scans (id, f, S11) VALUES
            (%s, %s, %s);
            """, (id, pickle.dumps(f), pickle.dumps(S11)))

conn.commit()

#read out what we put in there
cur.execute(
    """
    SELECT f
    FROM na_scans
    WHERE id=1
    """
)

fnew = pickle.loads(cur.fetchone()[0])
print(fnew)

cur.close()
conn.close()