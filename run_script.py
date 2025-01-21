# from take_data import take_data

# take_data(1000, 50, 2)

motor_steps_per_scan = 20000

import socket
from motor_control import send_command

# send the motor the instructions for turning one time
Message = "DI" + str(motor_steps_per_scan)
send_command(Message)

# send the motor the command to execute the previous instructions
Message = 'FL'
send_command(Message)