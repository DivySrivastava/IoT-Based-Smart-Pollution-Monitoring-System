import time
import datetime
import Netmaxiot
import math

from Adafruit_IO import Client 
USERNAME ="yogeshhindu"
KEY = "aio_OASZ047rQs0QRPqxsbCA11PrPqXt"
io = Client(USERNAME,KEY)
feed1 = io.feeds('lpg')  
feed3 = io.feeds("cogas")
feed2 = io.feeds("smoke") 

mq_pin= 3  # mq2 sensor place at the pin 3
RL_VALUE                     = 10      # define the load resistance on the board, in kilo ohms
RO_CLEAN_AIR_FACTOR          = 9.83    # RO_CLEAR_AIR_FACTOR=(Sensor resistance in clean air)/RO,
######################### Software Related Macros #########################
CALIBARAION_SAMPLE_TIMES     = 10  # define how many samples you are going to take in the calibration phase
CALIBRATION_SAMPLE_INTERVAL  = 5   # define the time interal(in milisecond) between each samples in the
READ_SAMPLE_INTERVAL         = 10  # define how many samples you are going to take in normal operation
READ_SAMPLE_TIMES            = 5  # define the time interal(in milisecond) between each samples in 
    ######################### Application Related Macros ######################
GAS_LPG                      = 0
GAS_CO                       = 1
GAS_SMOKE                    = 2
GAS_CO2                      = 3
GAS_COX                      = 4
LPGCurve = [2.3,0.21,-0.47] # data format:{ x, y, slope}; point1: (lg200, 0.21), point2: (lg10000, -0.59) 
COCurve = [2.3,0.72,-0.34] # data format:[ x, y, slope]; point1: (lg200, 0.72), point2: (lg10000,  0.15)
SmokeCurve =[2.3,0.53,-0.44]  # data format:[ x, y, slope]; point1: (lg200, 0.53), point2: (lg10000,  -0.22)  
CO2Curve = [2.3,0.50,-0.45]   # two points are taken from the curve.  mq 135 sensor 
COxCurve = [2.3,0.73,-0.43] # data format:[ x, y, slope]; point1: (lg200, 0.72), point2: (lg10000,  0.15)

def MQCalibration(mq_pin):
    val = 0
    for i in range(CALIBARAION_SAMPLE_TIMES):          # take multiple samples
        val += MQResistanceCalculation(mq_pin)
        val=round(val,2)                               # round of the value
        print ("the value of calib=",val)
        time.sleep(CALIBRATION_SAMPLE_INTERVAL/1000)
    val = val/CALIBARAION_SAMPLE_TIMES                 # calculate the average value
    val = val/RO_CLEAN_AIR_FACTOR                      # divided by RO_CLEAN_AIR_FACTOR yields the Ro 
    return val

def MQResistanceCalculation(mq_pin):
    raw_adc = Netmaxiot.analogRead(mq_pin)
    ax = (RL_VALUE*(1023-raw_adc))/raw_adc
    return ax

def MQRead(mq_pin):
    rs = 0
    for i in range(READ_SAMPLE_TIMES):
        rs += MQResistanceCalculation(mq_pin)
        time.sleep(READ_SAMPLE_INTERVAL/1000)
    rs = rs/READ_SAMPLE_TIMES
    return rs 


def MQPercentage(mq_pin):
    val = {}
    read = MQRead(mq_pin)
    val["GAS_LPG"]  = MQGetGasPercentage(read/Ro, GAS_LPG)
    val["CO"]       = MQGetGasPercentage(read/Ro, GAS_CO)
    val["SMOKE"]    = MQGetGasPercentage(read/Ro, GAS_SMOKE)
    return val

def MQGetPercentage(rs_ro_ratio, pcurve):
    return (math.pow(10,( ((math.log(rs_ro_ratio)-pcurve[1])/ pcurve[2]) + pcurve[0])))        


def MQGetGasPercentage(rs_ro_ratio, gas_id):
    if ( gas_id == GAS_LPG ):
        return MQGetPercentage(rs_ro_ratio, LPGCurve)
    elif ( gas_id == GAS_CO ):
        return MQGetPercentage(rs_ro_ratio, COCurve)
    elif ( gas_id == GAS_SMOKE ):
        return MQGetPercentage(rs_ro_ratio, SmokeCurve)
    elif ( gas_id == GAS_CO2 ):
        return MQGetPercentage(rs_ro_ratio, CO2Curve)    
    return 0              

print("Calibrating...Sensor 1")
Ro = MQCalibration(mq_pin)    # Ro resistance of Hydrogen for Mq2
print("Calibration is done...\n")
print("Rs/R0=%0.3f Ratio Resistance" %Ro)

while 1:
    perc = MQPercentage(mq_pin)
    zb= perc["GAS_LPG"]
    za =perc["CO"]
    zc =perc["SMOKE"]
    time.sleep(6)
    zb=round(zb,4)
    za=round(za,4)
    zc=round(zc,4)
    io.send(feed1.key,zb)
    io.send(feed2.key,za)
    io.send(feed3.key,zc)
    print ("the value of LPG gas",zb,"ppm")
    print ("the value of co gas",za,"ppm")
    print ("the value of Smoke ",zc,"ppm")
    print('++++++++++++++++++++++++++++')