import pyb
from pyb import Pin, Timer, ADC, DAC, LED
import time
from oled_938 import OLED_938
from mpu6050 import MPU6050
from motor import DRIVE
import micropython
micropython.alloc_emergency_exception_buf(100)

# I2C connected to Y9, Y10 (I2C bus 2) and Y11 is reset low active
oled = OLED_938(pinout={'sda': 'Y10', 'scl': 'Y9', 'res': 'Y8'}, height=64,
                   external_vcc=False, i2c_devid=61)
oled.poweron()
oled.init_display()

# IMU connected to X9 and X10
imu = MPU6050(1, False)     # Use I2C port 1 on Pyboard

motor=DRIVE()
pot = ADC(Pin('X11')) 


def pitch_estimate(pitch,dt,alpha):
    theta=imu.pitch()
    pitch_dot=imu.get_gy()
    pitch=alpha*(pitch+pitch_dot*dt*0.001)+(1-alpha)*theta
    return(pitch,pitch_dot)


trigger=pyb.Switch()
scaleP=10.0
scaleI=100
scaleD=20
"""
while not trigger():
    time.sleep(0.001)
    #K_p=pot.read()*scaleP/4095
    K_p=6.3
    #K_p=1.2
    oled.draw_text(0,30,'Kp={:5.2f}'.format(K_p))
    oled.display()
while trigger():pass
while not trigger():
    time.sleep(0.001)
    #K_i=pot.read()*scaleI/4095
    K_i=20
    oled.draw_text(0,40,'Ki={:5.2f}'.format(K_i))
    oled.display()
while trigger():pass
while not trigger():
    time.sleep(0.001)
    #K_d=pot.read()*scaleD/4095
    K_d=0.84
    oled.draw_text(0,50,'Kd={:5.2f}'.format(K_d))
    oled.display()
while trigger():pass
"""
print('Button pressed. Running script.')
oled.draw_text(0,20,'Button pressed. Running.')
oled.display()

alpha=0.77
error=0
e_integral=0
pitch=0
pitch_dot=0
w=0
offset=-3
e=0
K_d=0.87
K_i=15
K_p=6.3
tic=pyb.micros()
while True:
    dt=pyb.micros()-tic
    if dt>3000:
        #offset=pot.read()*200/4095
        #oled.draw_text(0,10,'offset={:5.2f}'.format(offset))
        #oled.display()
        #alpha=0.8
        pitch, pitch_dot = pitch_estimate(pitch,dt,alpha)
        e= pitch-offset
        w=(K_p*e + K_d*pitch_dot + K_i*e_integral)
        e_integral+=e
        if w<0:
            motor.right_forward(w)
            motor.left_forward(w)
        if w>0:
            motor.right_back(w)
            motor.left_back(w)
        
        tic=pyb.micros()


