
import pyb
from pyb import Pin, Timer, ADC, DAC, LED
from array import array
from oled_938 import OLED_938

#These lines are required for using interrupt
import micropython
micropython.alloc_emergency_exception_buf(100)


#####Dance Moves#####

from motor import MOTOR

motor_right=MOTOR()
motor_left=MOTOR()

def implement_move(current_dance_move):
    
    if current_dance_move==1:

        motor_right.A_forward(50)
        motor_left.B_forward(50)
    
    elif current_dance_move==2:

        motor_right.A_back(50)
        motor_left.B_back(50)
        
    elif current_dance_move==3:
     
        motor_right.A_forward(50)
        motor_left.B_back(30)
    
    elif current_dance_move==4:
       
        motor_right.A_back(50)
        motor_left.B_forward(30)
        
    elif current_dance_move==5:        
        motor_right.A_stop()
        motor_left.B_stop()
        
#######################################################
        
#wtf=0
# I2C connected to Y9, Y10 (I2C bus 2) and Y11 is reset low active
oled = OLED_938(pinout={'sda': 'Y10', 'scl': 'Y9', 'res': 'Y8'}, height=64,
                   external_vcc=False, i2c_devid=61)  
oled.poweron()
oled.init_display()
oled.draw_text(0,0, 'Beat Detection')
oled.display()

# define ports for microphone, LEDs and trigger out (X5)
mic = ADC(Pin('Y11'))
MIC_OFFSET = 1523    # ADC reading of microphone for silence
dac = pyb.DAC(1, bits=12)  # Output voltage on X5 (BNC) for debugging
b_LED = LED(4)      # flash for beats on blue LED

#This is the amount of samples that are taken by the microphone.
#These samples are taken every 8000/N amount of times per second
#This is sotred as an array
N = 100            # size of sample buffer s_buf[]

#This reserves memory in the buffer
s_buf = array('H', 0 for i in range(N))  # reserve buffer memory

#This line indicates to start the buffer from the zero positon which is the first value
ptr = 0             # sample buffer index pointer

#Set the flag of whether the microphone has recorded samples to zero
buffer_full = False # semaphore - ISR communicate with main program

##############################The Dance###############################
def flash():        # routine to flash blue LED when beat detected
    b_LED.on()
    pyb.delay(30)
    b_LED.off()
######################################################################
    
#######################Calculation for energy#########################
#Takes in all the readings from the buffer and computes the energy for them
def energy(buf):    # Compute energy of signal in buffer 
    sum = 0
    for i in range(len(buf)):
        s = buf[i] - MIC_OFFSET # adjust sample to remove dc offset
        sum = sum + s*s         # accumulate sum of energy
    return sum
######################################################################

#############################Interrupt###############################
# ---- The following section handles interrupts for sampling data -----
# Interrupt service routine to fill sample buffer s_buf
#This event is triggered in a calculated manner using the onboard timer of the PyBoard
def isr_sampling(dummy):    # timer interrupt at 8kHz
    global ptr              # need to make ptr visible inside ISR
    global buffer_full      # need to make buffer_full inside ISR
    
    #simply reads the microphone volume at that point in time - will return a value between 0-4095 after ADV conversion
    s_buf[ptr] = mic.read() # take a sample every timer interrupt
    ptr += 1                # increment buffer pointer (index)
    #When the microphone has continously collected enough samples (once every 125usec), then it will say that the buffer is fully and ready to be queried
    if (ptr == N):          # wraparound ptr - goes 0 to N-1
        ptr = 0
        buffer_full = True  # set the flag (semaphore) for buffer full
        
#################Setting the Timer & ISR to be called#################
# Create timer interrupt - one every 1/8000 sec or 125 usec
sample_timer = pyb.Timer(7, freq=8000)  # set timer 7 for 8kHz
sample_timer.callback(isr_sampling)     # specify interrupt service routine


########################Variables for adjusting readings##############
M = 50                 # number of instantaneous energy epochs to sum
BEAT_THRESHOLD = 4        # threshold for c to indicate a beat
SILENCE_THRESHOLD = 1.5     # threshold for c to indicate silence
######################################################################


# initialise variables for main program loop 
e_ptr = 0                   # pointer to energy buffer
e_buf = array('L', 0 for i in range(M)) # reserve storage for energy buffer
sum_energy = 0              # total energy in last 50 epochs


oled.draw_text(0,20, 'Ready to GO') # Useful to show what's happening?
oled.display()
pyb.delay(100)

tic = pyb.millis()          # mark time now in msec
######################################################################

#w = 1

while True:             # Main program loop
    if buffer_full:     # semaphore signal from ISR - set if buffer is full
        
        # Calculate instantaneous energy
        E = energy(s_buf)
        
        # compute moving sum of last 50 energy epochs
        #
        #This line is the moving average that acts as a low pass filter
        sum_energy = sum_energy - e_buf[e_ptr] + E
        e_buf[e_ptr] = E        # over-write earlest energy with most recent
        e_ptr = (e_ptr + 1) % M # increment e_ptr with wraparound - 0 to M-1
        
        # Compute ratio of instantaneous energy/average energy
        c = E*M/sum_energy
        #dac.write(min(int(c*4095/3), 4095))     # useful to see on scope, can remove
        if (pyb.millis()-tic > 400):    # if more than 500ms since last beat
            if (c>BEAT_THRESHOLD):      # look for a beat
                tic = pyb.millis()
                flash()
                #counter+=1
                #implement_move(current_dance_move)
                
                
                
        #dac.write(0)                    # sueful to see on scope, can remove
        buffer_full = False             # reset status flag

#Every 125usec the microphone records the audio
#When the audio has recorded a set number of samples, e.g. 160, then that means 0.2 seconds of audio has been recorded
#The energy of this audio is then calculated and returned as a single value called E
#A defined number of energy summations are made, e.g. 50, when 50 values have been reached the energy pointer resets and starts again,
##this is like forgeting the old data and moving the average
#The ratio of the current energy and the average energy are then compared to the arbitary value BEAT_THRESHOLD
#The pyb.millis just make sure that the loop is not constantly searching for a beat and getting mistriggered by offbeats
#When this BEAT_THRESHOLD is exceeded, the robot essentially dances
#Buffer full would remain true so needs to be reset
