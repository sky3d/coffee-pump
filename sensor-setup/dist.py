try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")
import time


print('init')
GPIO.setmode(GPIO.BCM)


mode = GPIO.getmode()
print(mode)

GPIO.setwarnings(False)

TRIG = 17
ECHO = 27

       
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
time.sleep(1)

print('start')
GPIO.output(TRIG, GPIO.HIGH)
time.sleep(0.00001)
GPIO.output(TRIG, GPIO.LOW)

print('echo 0')
while GPIO.input(ECHO) == False:
    start = time.time()
print('echo 1')
end = start
while GPIO.input(ECHO) == True:
    end = time.time()

print('calc')
sig_time = end - start
distance = sig_time / 0.000058 

print('Distance:  {} sm'.format(distance))

GPIO.cleanup()
