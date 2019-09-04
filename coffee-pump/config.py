C4R_HOST = 'cloud4rpi.io'
C4R_TOKEN = '__YOUR_DEVICE_TOKEN__'

NOTIFICATION_HOOK_URL = '__YOUR_HOOK_URL__'

# GPIO Pins
GPIO_PUMP = 4  # 7
GPIO_TRIGGER = 17
GPIO_ECHO = 27

# Distance from the sensor to the water level 
# based on the coffee-machine's water tank
MIN_DISTANCE = 1.5  # cm
MAX_DISTANCE = 8  # cm

# Take into account the inertion of the water when pump is off
STOP_PUMP_DISTANCE = 3  # cm

# Calibrate depending on the water level fluctuation
DISTANCE_DELTA = 0.4 # cm 
