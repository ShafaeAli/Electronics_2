import pyb
from pyb import Pin, Timer, ADC, UART
import motor2
from motor2 import MOTOR

motor_right=MOTOR()
motor_left=MOTOR()

uart = UART(6)
uart.init(9600, bits=8, parity = None, stop = 2)

while True:
    
    while (uart.any()!=10):    # wait for 10 chars
        pass
    command = uart.read(10)
    
    if command[2]==ord('5'):
        motor_right.A_forward(40)
        motor_left.B_forward(40)
    
    elif command[2] == ord('6'):
        motor_right.A_back(40)
        motor_left.B_back(40)
    
    elif command[2] == ord('7'):
        motor_right.A_forward(30)
        motor_left.B_back(20)
    
    elif command[2] == ord('8'):        
        motor_right.A_back(30)
        motor_left.B_forward(20)
        
    elif command[2] == ord('1'):        
        motor_right.A_stop()
        motor_left.B_stop()
       
    else:
        motor_right.A_stop()
        motor_left.B_stop()
    