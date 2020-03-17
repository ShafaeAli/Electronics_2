'''    Start of comment section
-------------------------------------------------------
Name: Basic Beat Detection implementation
Creator:  Peter YK Cheung
Date:   14 March 2017
Revision:  1.3
-------------------------------------------------------
This program do the following:
1. Use interrupt to collect samples from mic at 8kHz rate.
2. Compute instantenous energy E for 20msec window
3. Obtain sum of previous 50 instanteneous energy measurements
    as sum_energy, equivalent to 1 sec worth of signal.
4. Find the ratio c = instantenous energy/(sum_energy/50)
5. Wait for elapsed time > (beat_period - some margin) 
    since last detected beat 
6. Check c value and if higher than BEAT_THRESHOLD, 
    flash blue LED
'''    
import pyb
from pyb import Pin, Timer, ADC, DAC, LED
from array import array         # need this for memory allocation to buffers
from oled_938 import OLED_938   # Use OLED display driver

#  The following two lines are needed by micropython 
#   ... must include if you use interrupt in your program
import micropython
micropython.alloc_emergency_exception_buf(100)

# I2C connected to Y9, Y10 (I2C bus 2) and Y11 is reset low active
oled = OLED_938(pinout={'sda': 'Y10', 'scl': 'Y9', 'res': 'Y8'}, height=64,
                   external_vcc=False, i2c_devid=61)  
oled.poweron()
oled.init_display()
oled.draw_text(0,0, 'Beat Detection')
oled.display()

# define ports for microphone, LEDs and trigger out (X5)
mic = ADC(Pin('Y11'))
MIC_OFFSET = 1523       # ADC reading of microphone for silence
dac = pyb.DAC(1, bits=12)  # Output voltage on X5 (BNC) for debugging
b_LED = LED(4)      # flash for beats on blue LED

N = 10            # size of sample buffer s_buf[]
s_buf = array('H', 0 for i in range(N))  # reserve buffer memory
ptr = 0             # sample buffer index pointer
buffer_full = False # semaphore - ISR communicate with main program

def flash():        # routine to flash blue LED when beat detected
    b_LED.on()
    pyb.delay(30)
    b_LED.off()
    
def energy(buf):    # Compute energy of signal in buffer 
    sum = 0
    for i in range(len(buf)):
        s = buf[i] - MIC_OFFSET # adjust sample to remove dc offset
        sum = sum + s*s         # accumulate sum of energy
    return sum

# ---- The following section handles interrupts for sampling data -----
# Interrupt service routine to fill sample buffer s_buf
def isr_sampling(dummy):    # timer interrupt at 8kHz
    global ptr              # need to make ptr visible inside ISR
    global buffer_full      # need to make buffer_full inside ISR
    
    s_buf[ptr] = mic.read() # take a sample every timer interrupt
    ptr += 1                # increment buffer pointer (index)
    if (ptr == N):          # wraparound ptr - goes 0 to N-1
        ptr = 0
        buffer_full = True  # set the flag (semaphore) for buffer full

# Create timer interrupt - one every 1/8000 sec or 125 usec
sample_timer = pyb.Timer(7, freq=8000)  # set timer 7 for 8kHz
sample_timer.callback(isr_sampling)     # specify interrupt service routine

# -------- End of interrupt section ----------------

# Define constants for main program loop - shown in UPPERCASE
M = 1024                      # number of instantaneous energy epochs to sum
BEAT_THRESHOLD = 4.0        # threshold for c to indicate a beat
SILENCE_THRESHOLD = 1.3     # threshold for c to indicate silence

# initialise variables for main program loop 
e_ptr = 0                   # pointer to energy buffer
e_buf = array('L', 0 for i in range(M)) # reserve storage for energy buffer
sum_energy = 0              # total energy in last 50 epochs
oled.draw_text(0,20, 'Ready to GO') # Useful to show what's happening?
oled.display()
pyb.delay(100)
tic = pyb.millis()          # mark time now in msec

while True:             # Main program loop
    if buffer_full:     # semaphore signal from ISR - set if buffer is full
        
        # Calculate instantaneous energy
        E = energy(s_buf)
        
        # compute moving sum of last 50 energy epochs
        sum_energy = sum_energy - e_buf[e_ptr] + E
        e_buf[e_ptr] = E        # over-write earlest energy with most recent
        e_ptr = (e_ptr + 1) % M # increment e_ptr with wraparound - 0 to M-1
        
        # Compute ratio of instantaneous energy/average energy
        c = E*M/sum_energy
        #dac.write(min(int(c*4095/3), 4095))     # useful to see on scope, can remove
        
        if (pyb.millis()-tic > 400):    # if more than 500ms since last beat
            if (c>BEAT_THRESHOLD):      # look for a beat
                flash()                 # beat found, flash blue LED
                tic = pyb.millis()      # reset tic
        #dac.write(0)                    # sueful to see on scope, can remove
        buffer_full = False             # reset status flag
