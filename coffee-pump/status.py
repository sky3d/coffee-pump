
STATUS_MSG_ERR = 'Sensor Error!'
STATUS_MSG_OK = 'Water Level OK'
STATUS_MSG_POURING = 'Water pouring'
STATUS_MSG_OVERFLOW = 'Overflow!'

WATER_LEVEL_OVERFLOW_GAP = 20 # percent

def calc_status(error, percent, pump_on):
    return STATUS_MSG_ERR if error \
        else STATUS_MSG_OVERFLOW if percent > (100 + WATER_LEVEL_OVERFLOW_GAP) \
        else STATUS_MSG_POURING if pump_on \
        else STATUS_MSG_OK
