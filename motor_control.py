import socket

def send_command(message):
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
    Send a message to the motor
    '''
    Message = message
    print(Message)
    encodeMessage = Message.encode()
    Send = header + encodeMessage + end
    sock.sendto(Send, (D_IP, UDP_PORT))

