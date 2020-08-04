import smbus
import time

class ISL29125:

    #SL29125 I2C Address
    ISL_I2C_ADDR = 0x44

    #ISL29125 Registers
    DEVICE_ID = 0x00
    CONFIG_1  = 0x01
    CONFIG_2  = 0x02
    CONFIG_3 = 0x03
    THRESHOLD_LL = 0x04
    THRESHOLD_LH = 0x05
    THRESHOLD_HL = 0x06
    THRESHOLD_HH = 0x07
    STATUS = 0x08 
    GREEN_L = 0x09 
    GREEN_H = 0x0A
    RED_L  = 0x0B
    RED_H = 0x0C
    BLUE_L = 0x0D
    BLUE_H  =0x0E

    #Configuration Settings
    CFG_DEFAULT = 0x00

    #CONFIG1
    #Pick a mode, determines what color[s] the sensor samples, if any
    CFG1_MODE_POWERDOWN = 0x00
    CFG1_MODE_G = 0x01
    CFG1_MODE_R = 0x02
    CFG1_MODE_B = 0x03
    CFG1_MODE_STANDBY = 0x04
    CFG1_MODE_RGB = 0x05
    CFG1_MODE_RG = 0x06
    CFG1_MODE_GB = 0x07

    #Light intensity range
    #In a dark environment 375Lux is best, otherwise 10KLux is likely the best option
    CFG1_375LUX = 0x00
    CFG1_10KLUX = 0x08

    #Change this to 12 bit if you want less accuracy, but faster sensor reads
    #At default 16 bit, each sensor sample for a given color is about ~100ms
    CFG1_16BIT = 0x00
    CFG1_12BIT = 0x10

    #Unless you want the interrupt pin to be an input that triggers sensor sampling, leave this on normal
    CFG1_ADC_SYNC_NORMAL = 0x00
    CFG1_ADC_SYNC_TO_INT = 0x20

    #CONFIG2
    #Selects upper or lower range of IR filtering
    CFG2_IR_OFFSET_OFF = 0x00
    CFG2_IR_OFFSET_ON = 0x80

    #Sets amount of IR filtering, can use these presets or any value between 0x00 and 0x3F
    #Consult datasheet for detailed IR filtering calibration
    CFG2_IR_ADJUST_LOW = 0x00
    CFG2_IR_ADJUST_MID = 0x20
    CFG2_IR_ADJUST_HIGH = 0x3F

    #CONFIG3
    #No interrupts, or interrupts based on a selected color
    CFG3_NO_INT = 0x00
    CFG3_G_INT = 0x01
    CFG3_R_INT = 0x02
    CFG3_B_INT = 0x03

    #How many times a sensor sample must hit a threshold before triggering an interrupt
    #More consecutive samples means more times between interrupts, but less triggers from short transients
    CFG3_INT_PRST1 = 0x00
    CFG3_INT_PRST2 = 0x04
    CFG3_INT_PRST4 = 0x08
    CFG3_INT_PRST8 = 0x0C

    #If you would rather have interrupts trigger when a sensor sampling is complete, enable this
    #If this is disabled, interrupts are based on comparing sensor data to threshold settings
    CFG3_RGB_CONV_TO_INT_DISABLE = 0x00
    CFG3_RGB_CONV_TO_INT_ENABLE = 0x10

    #STATUS FLAG MASKS
    FLAG_INT  = 0x01
    FLAG_CONV_DONE = 0x02
    FLAG_BROWNOUT = 0x04
    FLAG_CONV_G = 0x10
    FLAG_CONV_R = 0x20
    FLAG_CONV_B = 0x30

    #Device commands
    RESET = 0x46

    def __init__(self, configVals=[0x0d,0x3f,0], bus=1):
        self.bus = smbus.SMBus(bus)
        data = self.bus.read_byte_data(ISL29125.ISL_I2C_ADDR,ISL29125.DEVICE_ID) #read device id
        if not(data == 0x7d):
            print("device with incorrect ID using address 0x44, check for conflict")
        output = self.reset() #reset all registers
        if output == -1:
            print("reset failed, could potentially have issues")
        output = self.config(configVals)


    def reset(self):
        self.bus.write_byte_data(ISL29125.ISL_I2C_ADDR, ISL29125.DEVICE_ID, ISL29125.RESET)
        data = self.bus.read_i2c_block_data(ISL29125.ISL_I2C_ADDR, ISL29125.CONFIG_1, 3) #read all config registers
        if sum(data) > 0:
            print("reset failed, config still applied")
            return -1
        data = self.bus.read_byte_data(ISL29125.ISL_I2C_ADDR, ISL29125.STATUS)
        if not(data == 0):
            print("reset failed, status non-zero")
            return -1

    def config(self, configVals):
        #write all 3 config registers with configVals list
        self.bus.write_i2c_block_data(ISL29125.ISL_I2C_ADDR, ISL29125.CONFIG_1, configVals)
        checkWrite = self.bus.read_i2c_block_data(ISL29125.ISL_I2C_ADDR, ISL29125.CONFIG_1, 3)
        if not(checkWrite == configVals):
            print("write and verifying config registers failed")
            return -1
        return 0

    @property
    def upperThreshold(self):
        try:
            val = self.bus.read_i2c_block_data(ISL29125.ISL_I2C_ADDR, ISL29125.THRESHOLD_HL,2)
            return (val[1]<<8|val[0])
        except IOError:
            print("error with i2c")
            return -1
    #value is a list with 2 bytes 
    @upperThreshold.setter
    def upperThreshold(self, value):
        try:
            self.bus.write_i2c_block_data(ISL29125.ISL_I2C_ADDR, ISL29125.THRESHOLD_HL, value)
            return 0
        except IOError:
            print("error with i2c")
            return -1
    
    @property
    def lowerThreshold(self):
        try:
            val = self.bus.read_i2c_block_data(ISL29125.ISL_I2C_ADDR, ISL29125.THRESHOLD_LL,2)
            return (val[1]<<8|val[0])
        except IOError:
            print("error with i2c")
            return -1
    #value is a list with 2 bytes 
    @lowerThreshold.setter
    def lowerThreshold(self, value):
        try:
            self.bus.write_i2c_block_data(ISL29125.ISL_I2C_ADDR, ISL29125.THRESHOLD_LL, value)
            return 0
        except IOError:
            print("error with i2c")
            return -1

    @property
    def rgbVal(self):
        try:
            out = self.bus.read_i2c_block_data(ISL29125.ISL_I2C_ADDR, ISL29125.GREEN_L, 6)
            r = out[3]<<8|out[2]
            g = out[1]<<8|out[0] 
            b = out[5]<<8|out[4]
            return [r,g,b]
        except IOError:
            print("error with rgb sensor i2c read")
            return [-1,-1,-1]

    @property
    def isl29125_status(self):
        try:
            out = self.bus.read_byte_data(ISL29125.ISL_I2C_ADDR, ISL29125.STATUS)
            return out
        except IOError:
            return -1