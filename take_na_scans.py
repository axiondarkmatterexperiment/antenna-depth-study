from cavity_fit import reflection_fit, transmission_fit
from Lorentz_function import dip_func, peak_func
import pyvisa
import time
import numpy as np
import matplotlib.pyplot as plt

# connect to the network analyzer and ask what state it's in
rm = pyvisa.ResourceManager()
inst = rm.open_resource('TCPIP0::localhost::TCPIP0::INSTR')
print(inst.query("TRIG:SOUR?"))
print(inst.query("TRIG:STAT?"))



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
# plt.savefig("C:\\Users\\senna\\OneDrive\\Documents\\UW\\ADMX\\plot_trans.pdf", format = 'pdf', bbox_inches = 'tight')

time.sleep(1)

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
time.sleep(1)

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
time.sleep(1)


# fit parameters to the data
pt, pc, beta = reflection_fit(f,S11_real, S11_imag, S11_phase)
f0_refl = pt[2]

print("measured beta:")
print(beta)