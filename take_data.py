import psycopg2
import pickle
import socket
import pyvisa
import numpy as np
import scipy
from cavity_fit import reflection_fit, transmission_fit
from Lorentz_function import dip_func, peak_func
import matplotlib.pyplot as plt
import time

def take_data(motor_steps_per_scan, num_scans, num_cycles):
    ''' 
    Set up connections to the psql database, VNA, and motor
    '''

    # define the connection to the postgres database
    conn = psycopg2.connect(host='localhost', dbname='postgres', user='postgres', password='axionsrock', port=5432)

    #I think this is just what we use to send commands directly to the postgres command line
    cur = conn.cursor()

    #Send the command to create the datatable in the postgres database. Here we type things just like queries in the postgres command line
    cur.execute("""CREATE TABLE IF NOT EXISTS na_scans(
                id INT PRIMARY KEY,
                f BYTEA,
                S11_real BYTEA,
                S11_imag BYTEA,
                S11_phase BYTEA,
                S21_real BYTEA,
                S21_imag BYTEA,
                f0_trans REAL,
                f0_refl REAL,
                QL_trans REAL,
                beta REAL
                );
                """)

    # connect to the network analyzer and ask what state it's in
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource('TCPIP0::localhost::TCPIP0::INSTR')
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


    '''
    
    Begin data taking cycles
    
    '''
    
    cur.execute("SELECT id FROM na_scans ORDER BY id DESC;")
    try: 
        id=cur.fetchone()[0]
    except:
        id = 0
    id = id+1

    for n in np.arange(num_cycles):
        for m in np.arange(num_scans):

            '''
            
            Read the motor position
            
            '''

            # # send the motor the instructions for turning one time
            # Message = "SK" #I think this might be the right command?
            # encodeMessage = Message.encode()
            # Send = header + encodeMessage + end
            # sock.sendto(Send, (D_IP, UDP_PORT))
            
            # Message = "EP" #I think this might be the right command?
            # encodeMessage = Message.encode()
            # Send = header + encodeMessage + end
            # sock.sendto(Send, (D_IP, UDP_PORT))
            # recMessage = sock.recv(2048).decode()
            # print("motor steps "+recMessage)
            # motor_steps = int(recMessage[5:])

            ''''
            
            Set VNA trigger
            
            '''

            inst.write("TRIG:SOUR BUS")
            inst.write("TRIG:WAIT WTRG")
            time.sleep(0.5)
            # inst.write('TRIG:SING')
            # inst.write('CALC1:TRAC2:FORM UPH')

            '''
            transmission scan:
            '''
            # Take a transmission scan and record the frequency and S21 arrays
            inst.write("CALC1:PAR1:DEF S21") #take a transmission scan
            time.sleep(0.5)
            inst.write('CALC1:FORM MLOG') #Set the form of the data to log magnitude
            time.sleep(0.5)
            inst.write('DISP:WIND1:TRAC:Y:AUTO')
            time.sleep(0.2)
            f = [inst.query('SENS1:FREQ:DATA?')] #read out the frequency array
            f_str = inst.query('SENS1:FREQ:DATA?')
            f = f_str.split(',')
            f = np.asarray(f)
            f = np.single(f)
            S21_str = inst.query('SENS1:DATA:CORR? S21') #read out the S21 log powers
            S21 = S21_str.split(',')
            S21 = np.asarray(S21)
            S21 = np.single(S21)
            S21 = np.reshape(S21,(int(np.size(S21)/2),2))
            S21_imag = S21[:, 0]
            S21_real = S21[:, 1]

            '''
            fitting transmission
            '''
            # find a best fit for the transmission data
            pt, pc = transmission_fit(f,S21_real, S21_imag)

            # save the variables from the transmission fit. These will be used for guesses in the reflection fit
            f0_trans = pt[2]
            QL_trans = pt[1]
            print("resonant frequency from transmission:")
            print(f0_trans)
            print("loaded Q from transmission:")
            print(QL_trans)

            pt_trans, pc_trans = transmission_fit(f,S21_real, S21_imag)
            plt.figure(figsize=(12,9))
            plt.plot(f, peak_func(f, *pt_trans))
            plt.plot(f, np.add(np.square(S21_real), np.square(S21_imag)))
            plt.savefig("C:\\Users\\senna\\OneDrive\\Documents\\UW\\ADMX\\plot_trans.pdf", format = 'pdf', bbox_inches = 'tight')
            
            time.sleep(5)

            '''
            adjust the scan window
            '''
            #Set the center frequency and the width of the reflection scan (this will be held onto by the VNA into the next transmission scan, too.)
            Q_width = np.abs(f0_trans/QL_trans)
            window_size = 8*Q_width
            print("window size:")
            print(window_size)
            inst.write("SENS1:FREQ:SPAN "+str(window_size))
            inst.write("SENS1:FREQ:CENT "+str(f0_trans))
            inst.write("TRIG:SING")
            time.sleep(0.5)


            '''
            Reflection scan
            '''
            inst.write("CALC1:PAR1:DEF S11") #take a reflection scan in trace 1 of channel 1
            time.sleep(0.5)
            inst.write('DISP:WIND1:TRAC:Y:AUTO')
            time.sleep(0.2)
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
            time.sleep(5)

            inst.write("CALC1:TRAC1:FORM UPH")
            inst.write('DISP:WIND1:TRAC:Y:AUTO')
            time.sleep(0.2)
            S11_phase = [inst.query('CALC1:TRAC1:DATA:FDAT?')]
            S11_phase_str = inst.query('CALC1:TRAC1:DATA:FDAT?')
            S11_phase = S11_phase_str.split(',')
            S11_phase = np.asarray(S11_phase)
            S11_phase = np.single(S11_phase)
            S11_phase = np.reshape(S11_phase,(int(np.size(S11_phase)/2),2))
            S11_phase = S11_phase[:, 0]
            time.sleep(5)

            
            # fit parameters to the data
            pt, pc, beta = reflection_fit(f,S11_real, S11_imag, S11_phase)
            f0_refl = pt[2]

            time.sleep(5)

            '''
            save data to PSQL table
            '''
            # insert the variables above into the table we created.
            # the numpy arrays need to be saved as BYTEA datatype which is what the pickle dumps function converts them into
            cur.execute("""INSERT INTO na_scans (id, f, S11_real, S11_imag, S11_phase, S21_real, S21_imag, f0_trans, f0_refl, QL_trans, beta) VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                        """, (id, pickle.dumps(f), pickle.dumps(S11_real), pickle.dumps(S11_imag), pickle.dumps(S11_phase), pickle.dumps(S21_real), pickle.dumps(S21_imag), np.abs(f0_trans), np.abs(f0_refl), np.abs(QL_trans), np.abs(beta)))

            # I think this is just to actually submit these commands to the postgres command line, but I'm not sure
            conn.commit()

            '''
            Move the motor
            '''
            # send the motor the instructions for turning one time
            Message = "DI" + str(motor_steps_per_scan)
            print(Message)
            encodeMessage = Message.encode()
            Send = header + encodeMessage + end
            sock.sendto(Send, (D_IP, UDP_PORT))

            # send the motor the command to execute the previous instructions
            Message = 'FL'
            encodeMessage = Message.encode()
            Send = header + encodeMessage + end
            sock.sendto(Send, (D_IP, UDP_PORT))
            time.sleep(np.abs(motor_steps_per_scan)/2000)

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

            print("beta is:")
            print(beta)
            id = id+1
        motor_steps_per_scan=-motor_steps_per_scan
            

    # close the database
    cur.close()
    conn.close()
