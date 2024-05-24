import psycopg2
import pickle
import numpy as np

#define the connection to the postgres database
conn = psycopg2.connect(host='localhost', dbname='postgres', user='postgres', password='axionsrock', port=5432)

#I think this is just what we use to send commands directly to the postgres command line
cur = conn.cursor()

#Send the command to create the datatable in the postgres database. Here we type things just like queries in the postgres command line
cur.execute("""CREATE TABLE IF NOT EXISTS na_scans(
            id INT PRIMARY KEY,
            f BYTEA,
            S11 BYTEA
);
            """)

#these are just some variables I came up with for the tutorial
id = 1
f = np.asarray([1.31, 1.32, 1.33])
S11 = np.asarray([21, 19, 22])

#Insert the variables above into the table we created.
# The numpy arrays need to be saved as BYTEA datatype which is what the pickle dumps function converts them into
cur.execute("""INSERT INTO na_scans (id, f, S11) VALUES
            (%s, %s, %s);
            """, (id, pickle.dumps(f), pickle.dumps(S11)))

#I think this is just to actually submit these commands to the postgres command line, but I'm not sure.
conn.commit()

#read out what we put in there
cur.execute(
    """
    SELECT f
    FROM na_scans
    WHERE id=1
    """
)

#Convert the numpy array f back into a numpy array from the BYTEA datatype.
# I'm not totally sure about the syntax of the fetchone command.
fnew = pickle.loads(cur.fetchone()[0])
print(fnew)

cur.close()
conn.close()
