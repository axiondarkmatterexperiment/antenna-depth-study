import socket
import pyvisa
import numpy as np
import scipy

rm = pyvisa.ResourceManager()
inst = rm.open_resource('TCPIP0::localhost::TCPIP0::INSTR')
# inst.query("TRIG:SOUR BUS")
print(inst.query("TRIG:SOUR?"))
print(inst.query("TRIG:STAT?"))

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
HOST = '10.10.10.11'
UDP_PORT = 7775
D_IP = '10.10.10.10'
sock.bind((HOST, 7775))

header = bytes(([0x00, 0x07]))
end = bytes([0xD])

Message = 'DI20000'
encodeMessage = Message.encode()
Send = header + encodeMessage + end
sock.sendto(Send, (D_IP, UDP_PORT))

Message = 'FL'
encodeMessage = Message.encode()
Send = header + encodeMessage + end
sock.sendto(Send, (D_IP, UDP_PORT))

inst.write('TRIG:SING')
print(inst.query('SENS1:FREQ:DATA?'))
inst.write("TRIG:WAIT WTRG")
print(inst.query("TRIG:STAT?"))

recMessage = sock.recv(1024).decode()
print(recMessage[2:])