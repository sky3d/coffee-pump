from config import SENSOR_ERROR, NO_WATER_ERROR

def calc_status(error_code, percent, pump_on):
    return 'Sensor Error!' if error_code == SENSOR_ERROR \
        else 'Empty Water Source!' if error_code == NO_WATER_ERROR \
        else 'Water pouring' if pump_on \
        else 'Low Water Level' if percent < 25 \
        else 'Overflow!' if percent > 100 \
        else 'Water Level OK'


def calc_alert(error_code):
    sensor_msg = 'WARNING! The sensor probably is out of order...'
    no_water_msg ='ACTION REQUIRED! Replace a water bottle and enable the pump by adding water manually.'
    return sensor_msg if error_code == SENSOR_ERROR \
        else no_water_msg if error_code == NO_WATER_ERROR \
        else ''
