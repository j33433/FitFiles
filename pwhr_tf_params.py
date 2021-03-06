
'''
pwhr_tf_params.py

Estimate parameters for the power-HR transfer function:
    FTHR            : Functional threshold heart rate, BPM
    HRTimeConstant  : First-order time constant for heart rate, sec
    HRDriftRate     : Fatigue-induced cardiac drift rate, BPM/TSS

'''

import os
import sys
import time

class PrintAndFileStream():
    "A class that prints to stdout as well as to file"
    def __init__(self, OutFileName):
        self.OutFile = open(OutFileName, 'a')
    def write(self, data):
        print data,
        print >> self.OutFile, data,
    def flush(self):
        self.OutFile.flush()
    def close(self):
        self.OutFile.close()


############################################################
#               pwhr_tf_params function def                #
############################################################

#def pwhr_tf_params(FitFilePath, ConfigFile=None, OutStream=sys.stdout):

#ConfigFile  = r'D:\Users\Owner\Documents\OneDrive\2018\fitfiles\\'  \
ConfigFile  = r'S:\will\documents\OneDrive\2018\fitfiles\\'  \
            + r'cyclingconfig_kim.txt'
#OutStream   = sys.stdout
OutStream   = PrintAndFileStream('output.txt')

FilePath    = r'S:\will\documents\OneDrive\bike\activities\kim\\'
fit_files   = [ '2018-09-10-18-21-11.fit' ,   # A2
                '2018-06-22-18-35-17.fit' ,   # M2
                '2018-08-25-17-27-32.fit' ,   # M6
                '2018-09-24-18-27-54.fit' ,   # M6
                '2018-09-06-18-23-46.fit' ,   # M1
                '2018-12-26-14-51-33.fit'     # E2
              ] #[2:3]

#(FilePath, FitFileName) = os.path.split(FitFilePath)

if ConfigFile is None:
    # attempt to find appropriate config file
    if 'will' in FilePath.split('\\'):
        ConfigFile = FilePath + r'\cyclingconfig_will.txt'
        print >> OutStream, 'ConfigFile:'
        print >> OutStream, ConfigFile
    elif 'kim' in FilePath.split('\\'):
        ConfigFile = FilePath + r'\cyclingconfig_kim.txt'
if (ConfigFile is None) or (not os.path.exists(ConfigFile)):
    raise IOError('Configuration file not specified or found')

#
#   Parse the configuration file
#
from ConfigParser import ConfigParser
config      = ConfigParser()
config.read(ConfigFile)
print >> OutStream, 'reading config file ' + ConfigFile
WeightEntry     = config.getfloat( 'user', 'weight' )
WeightToKg      = config.getfloat( 'user', 'WeightToKg' )
weight          = WeightEntry * WeightToKg
age             = config.getfloat( 'user', 'age' )
EndurancePower  = config.getfloat( 'power', 'EndurancePower' )
ThresholdPower  = config.getfloat( 'power', 'ThresholdPower' )
EnduranceHR     = config.getfloat( 'power', 'EnduranceHR'    )
ThresholdHR     = config.getfloat( 'power', 'ThresholdHR'    )
HRTimeConstant  = config.getfloat( 'power', 'HRTimeConstant' )
HRDriftRate     = config.getfloat( 'power', 'HRDriftRate'    )
print >> OutStream, 'WeightEntry    : ', WeightEntry
print >> OutStream, 'WeightToKg     : ', WeightToKg
print >> OutStream, 'weight         : ', weight
print >> OutStream, 'age            : ', age
print >> OutStream, 'EndurancePower : ', EndurancePower
print >> OutStream, 'ThresholdPower : ', ThresholdPower
print >> OutStream, 'EnduranceHR    : ', EnduranceHR
print >> OutStream, 'ThresholdHR    : ', ThresholdHR
print >> OutStream, 'HRTimeConstant : ', HRTimeConstant
print >> OutStream, 'HRDriftRate    : ', HRDriftRate
FTP     = ThresholdPower
FTHR    = ThresholdHR



from fitparse import Activity
from activity_tools import extract_activity_signals
from endurance_summary import BackwardMovingAverage
from scipy.integrate import odeint
from scipy.optimize import minimize
import numpy as np

required_signals    = [ 'power',
                        'heart_rate' ]

SampleRate  = 1.0

PwHRTable   = np.array( [
                [    0    ,  0.50*FTHR ],   # Active resting HR
                [ 0.55*FTP,  0.70*FTHR ],   # Recovery
                [ 0.70*FTP,  0.82*FTHR ],   # Aerobic threshold
                [ 1.00*FTP,       FTHR ],   # Functional threshold
                [ 1.20*FTP,  1.03*FTHR ],   # Aerobic capacity
                [ 1.50*FTP,  1.06*FTHR ]])  # Max HR

def heartrate_dot(HR, t, FTHR, HRTimeConstant, sHRDriftRate):
    ''' Heart rate model. The derivative, the return value, is
        proportional to the difference between the HR target and
        the current heartrate.
    '''
    PwHRTable[0,1]  = 0.50*FTHR     # Active resting HR
    PwHRTable[1,1]  = 0.70*FTHR     # Recovery
    PwHRTable[2,1]  = 0.82*FTHR     # Aerobic threshold
    PwHRTable[3,1]  =      FTHR     # Functional threshold
    PwHRTable[4,1]  = 1.03*FTHR     # Aerobic capacity
    PwHRTable[5,1]  = 1.06*FTHR     # Max HR
    #print '    heartrate_dot called'
    HRDriftRate = sHRDriftRate/1000.0
    i = min( int(t * SampleRate), nScans-1 )
    HRp = np.interp( power[i], PwHRTable[:,0], PwHRTable[:,1] )
    HRt = HRp + HRDriftRate*TSS[i]
    return ( HRt - HR ) / HRTimeConstant


def HRSimulationError(params):
    ''' A function passed to scipy.optimize.minimize() that
        computes and returns the error in simulating heart rate
        based on the three parameters passed to it.
            FTHR            = params[0]
            HRTimeConstant  = params[1]
            sHRDriftRate    = params[2]
    '''
    args            = tuple(params)
    heart_rate_sim  = odeint( heartrate_dot,
                              heart_rate_ci[0],
                              time_ci,
                              args=args )
    err     = np.squeeze( heart_rate_sim ) \
            - np.squeeze( heart_rate_ci  )
    RMSError    = np.sqrt(np.average( err[time_idx]**2 ))
    print >> OutStream, \
        'HRSimulationError called with %10i, %10.1f, %10.3f -> %10.3f' \
        % (params[0], params[1], params[2], RMSError)
    return RMSError


print >> OutStream, 'Optimization Results:'
names1  = [ 'FIT File', 'FTHR (BPM)',  'tau (sec)', 'sHRDriftRate' ]
fmt     = '%20s:' + '%15s'*3
print >> OutStream, fmt % tuple(names1)
OutStream.flush()

for FitFile in fit_files:

    TimerStart = time.time()     # measure execution time

    print >> OutStream, '#################################################'
    print >> OutStream, '###%s###' % FitFile.center(43)
    print >> OutStream, '#################################################'

    # get the signals
    FitFilePath = FilePath + FitFile
    activity    = Activity(FitFilePath)
    signals     = extract_activity_signals(activity, resample='existing')

    if not all( s in signals.keys() for s in required_signals ):
        msg = 'required signals not in file'
        print >> OutStream, msg
        print >> OutStream, 'Signals required:'
        for s in required_signals:
            print >> OutStream, '   ' + s
        print >> OutStream, 'Signals contained:'
        for s in signals.keys():
            print >> OutStream, '   ' + s
        raise IOError(msg)

    # resample to constant-increment (1 Hz) with zeros at missing samples
    time_idx                = signals['time'].astype('int')
    power_vi                = signals['power']
    heart_rate_vi           = signals['heart_rate']
    nScans                  = time_idx[-1]+1
    time_ci                 = np.arange(nScans)
    power                   = np.zeros(nScans)
    power[time_idx]         = power_vi
    heart_rate_ci           = np.zeros(nScans)
    heart_rate_ci[time_idx] = heart_rate_vi

    # compute the 30-second, moving-average power signal.
    p30 = BackwardMovingAverage( power )

    # Calculate running normalized power and TSS.
    norm_power  = np.zeros(nScans)
    TSS         = np.zeros(nScans)
    for i in range(1,nScans):
        norm_power[i] = np.average( p30[:i]**4 )**(0.25)
        TSS[i] = time_ci[i]/36*(norm_power[i]/FTP)**2
    OutStream.flush()

    # optimize by minimizing the simulation error
    # Scale HRDriftRate to same order of magnitude as other parameters.
    x0  = [ ThresholdHR, HRTimeConstant, 1000*HRDriftRate ]
    bnds = ( (130.0, 200.0), (30.0, 120.0), (0.0, 500.0) )
    res = minimize( HRSimulationError, x0,
                    method='Nelder-Mead',
                    options={'xatol': 1.0, 'fatol': 1.0} )
    #print res.message
    fmt     = '%20s:' + '%10i' + '%10.1f' + '%10.3f'
    print >> OutStream, fmt % (FitFile, res.x[0], res.x[1], res.x[2] )
    print >> OutStream, res

    TimerEnd    = time.time()
    ExTime      = TimerEnd - TimerStart
    mm  = ExTime // 60
    ss  = ExTime % 60
    print >> OutStream, 'Results for %s:' % FitFile
    print >> OutStream, '    execution time = %02i:%02i' % (mm, ss)
    print >> OutStream, '    ThresholdHR     :%8.1f ; BPM    ' % res.x[0]
    print >> OutStream, '    HRTimeConstant  :%8.1f ; seconds' % res.x[1]
    print >> OutStream, '    HRDriftRate     :%8.3f ; BPM/TSS' % (res.x[2]/1e3)
    OutStream.flush()

if OutStream is not sys.stdout:
    OutStream.close()

# end pwhr_tf_params()

#############################################################
##           main program execution                         #
#############################################################
#'''
#This technique allows the module to be imported without
#executing it until one of its functions is called.
#'''
#
#if __name__ == '__main__':
#    import sys
#    if len(sys.argv) >= 2:
#        print 'command line args: ', sys.argv[1:]
#        fitfilepath = sys.argv[1]
#        pwhr_transfer_function(fitfilepath, ConfigFile=None)
#    else:
#        raise IOError('Need a .FIT file')

## VO2max intervals:
#FitFilePath = r'S:\will\documents\OneDrive\bike\activities\will\\' \
#            + r'2018-12-10-17-28-24.fit'
## threshold effort:
#FitFilePath = r'S:\will\documents\OneDrive\bike\activities\will\\' \
#            + r'2018-09-03-17-36-11.fit'
## threshold intervals:
#FitFilePath = r'S:\will\documents\OneDrive\bike\activities\will\\' \
#            + r'2018-07-17-15-12-10.fit'
## endurance:
#FitFilePath = r'S:\will\documents\OneDrive\bike\activities\will\\' \
#            + r'2018-12-31-12-23-12.fit'
# no heartrate signal
#FitFilePath = r'S:\will\documents\OneDrive\bike\activities\will\\' \
#            + r'2018-12-22-16-28-06.fit'
