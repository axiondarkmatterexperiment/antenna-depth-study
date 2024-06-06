import psycopg2
import pickle
import socket
import pyvisa
import numpy as np
import scipy
from cavity_fit import reflection_fit, transmission_fit
from Lorentz_function import dip_func, peak_func
import matplotlib.pyplot as plt

# define the connection to the postgres database
conn = psycopg2.connect(host='localhost', dbname='postgres', user='postgres', password='axionsrock', port=5432)

#I think this is just what we use to send commands directly to the postgres command line
cur = conn.cursor()
cur.execute('DROP TABLE na_scans;')

#Send the command to create the datatable in the postgres database. Here we type things just like queries in the postgres command line
cur.execute("""CREATE TABLE IF NOT EXISTS na_scans(
            id INT PRIMARY KEY,
            f BYTEA,
            S11_real BYTEA,
            S11_imag BYTEA,
            S11_phase BYTEA,
            S21_real BYTEA,
            S21_imag BYTEA
);
            """)

# connect to the network analyzer and ask what state it's in
rm = pyvisa.ResourceManager()
inst = rm.open_resource('TCPIP0::localhost::TCPIP0::INSTR')
inst.write("TRIG:SOUR BUS")
print(inst.query("TRIG:SOUR?"))
print(inst.query("TRIG:STAT?"))

# connect to the motor
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
HOST = '10.10.10.11'
UDP_PORT = 7775
D_IP = '10.10.10.10'
sock.bind((HOST, 7775))

# define a script for talking to the motor
header = bytes(([0x00, 0x07]))
end = bytes([0xD])

# send the motor the instructions for turning one time
Message = 'DI20000'
encodeMessage = Message.encode()
Send = header + encodeMessage + end
#sock.sendto(Send, (D_IP, UDP_PORT))

# send the motor the command to execute the previous instruction
Message = 'FL'
encodeMessage = Message.encode()
Send = header + encodeMessage + end
#sock.sendto(Send, (D_IP, UDP_PORT))

# tell the NA to take a transmission scan and print the data
print(inst.query('SENS1:DATA:CORR? S21'))

# define frequency and transmission power as arrays to be sent to the database in a table
f = [inst.query('SENS1:FREQ:DATA?')]
f_str = inst.query('SENS1:FREQ:DATA?')
f = f_str.split(',')
f = np.asarray(f)
f = np.single(f)
S21_str = inst.query('SENS1:DATA:CORR? S21')
S21 = S21_str.split(',')
S21 = np.asarray(S21)
S21 = np.single(S21)
S21 = np.reshape(S21,(int(np.size(S21)/2),2))
S21_imag = S21[:, 0]
S21_real = S21[:, 1]

# find a best fit for the transmission data and plot it
pt, pc = transmission_fit(f,S21_real, S21_imag)
plt.figure(figsize=(12,9))
plt.plot(f, peak_func(f, *pt))
plt.plot(f, np.add(np.square(S21_real), np.square(S21_imag)))
plt.savefig("C:\\Users\\senna\\OneDrive\\Documents\\UW\\ADMX\\plot_q.pdf", format = 'pdf', bbox_inches = 'tight')
print(pt[1])

# tell the NA to take a reflection scan and print the data
inst.write('TRIG:SING')
print(inst.query('*OPC?'))
print(inst.query('SENS1:DATA:CORR? S11'))
inst.write('CALC1:TRAC2:FORM UPH')
print(inst.query('CALC1:TRAC2:FORM?'))
print(inst.query('CALC1:TRAC2:DATA:FDAT?'))

# define frequency and power as arrays to be sent to the database in a table
id = 1
f = [inst.query('SENS1:FREQ:DATA?')]
f_str = inst.query('SENS1:FREQ:DATA?')
f = f_str.split(',')
f = np.asarray(f)
f = np.single(f)
S11_str = inst.query('SENS1:DATA:CORR? S11')
S11 = S11_str.split(',')
S11 = np.asarray(S11)
S11 = np.single(S11)
S11 = np.reshape(S11,(int(np.size(S11)/2),2))
S11_imag = S11[:, 0]
S11_real = S11[:, 1]
S11_phase = [inst.query('CALC1:TRAC2:DATA:FDAT?')]
S11_phase_str = inst.query('CALC1:TRAC2:DATA:FDAT?')
S11_phase = S11_phase_str.split(',')
S11_phase = np.asarray(S11_phase)
S11_phase = np.single(S11_phase)
S11_phase = np.reshape(S11_phase,(int(np.size(S11_phase)/2),2))
S11_phase = S11_phase[:, 0]

# insert the variables above into the table we created.
# the numpy arrays need to be saved as BYTEA datatype which is what the pickle dumps function converts them into
cur.execute("""INSERT INTO na_scans (id, f, S11_real, S11_imag, S11_phase, S21_real, S21_imag) VALUES
            (%s, %s, %s, %s, %s, %s, %s);
            """, (id, pickle.dumps(f), pickle.dumps(S11_real), pickle.dumps(S11_imag), pickle.dumps(S11_phase), pickle.dumps(S21_real), pickle.dumps(S21_imag)))

# I think this is just to actually submit these commands to the postgres command line, but I'm not sure
conn.commit()

# read out what we put in there
cur.execute(
    """
    SELECT f
    FROM na_scans
    WHERE id=1
    """
)

# convert the numpy array f back into a numpy array from the BYTEA datatype
# I'm not totally sure about the syntax of the fetchone command
fnew = pickle.loads(cur.fetchone()[0])
print(fnew)

# tell the motor to go back to waiting and confirm that it's now waiting again
inst.write("TRIG:WAIT WTRG")
print(inst.query("TRIG:STAT?"))

# print any messages that the motor is sending back
# recMessage = sock.recv(1024).decode()
# print(recMessage[2:])

# pow = np.add(np.square(S11_imag), np.square(S11_real))
# pow = 10*(np.log10(pow))
# plt.figure(figsize=(12,9))
# plt.plot(f, pow)
# plt.savefig("C:\\Users\\senna\\OneDrive\\Documents\\UW\\ADMX\\plot.pdf", format = 'pdf', bbox_inches = 'tight')

# fit parameters to the data
pt, pc, beta = reflection_fit(f,S11_real, S11_imag, S11_phase)
plt.figure(figsize=(12,9))
plt.plot(f, dip_func(f, *pt))
plt.plot(f, np.add(np.square(S11_real), np.square(S11_imag)))
plt.savefig("C:\\Users\\senna\\OneDrive\\Documents\\UW\\ADMX\\plot.pdf", format = 'pdf', bbox_inches = 'tight')

plt.figure(figsize=(12,9))
plt.plot(f, S11_phase)
# plt.plot(f, S11_imag)
# plt.plot(f, S11_real)
plt.savefig("C:\\Users\\senna\\OneDrive\\Documents\\UW\\ADMX\\plot_imag.pdf", format = 'pdf', bbox_inches = 'tight')

#print beta
print(beta)

# close the database
cur.close()
conn.close()
