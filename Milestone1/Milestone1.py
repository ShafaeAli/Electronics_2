import pyb
from pyb import Pin, Timer, ADC, UART
import motor
from motor import MOTOR

motor_right=MOTOR()
motor_left=MOTOR()

uart = UART(6)
uart.init(9600, bits=8, parity = None, stop = 2)

while True:
    
    while (uart.any()!=10):    # wait for 10 chars
        pass
    command = uart.read(10)
    
    if command[2]==ord('5'):
        motor_right.A_forward(50)
        motor_left.B_forward(50)
    
    elif command[2] == ord('6'):
        motor_right.A_back(50)
        motor_left.B_back(50)
    
    elif command[2] == ord('7'):
        motor_right.A_forward(30)
        motor_left.B_back(30)
    
    elif command[2] == ord('8'):        
        motor_right.A_back(30)
        motor_left.B_forward(30)
        
    elif command[2] == ord('1'):        
        motor_right.A_stop()
        motor_left.B_stop()
       
    else:
        motor_right.A_stop()
        motor_left.B_stop()
    