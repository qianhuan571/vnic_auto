import os, signal, sys, subprocess, time
from ctypes import *


def signal_handler(signal, frame):
    #print 'Ctrl+C received in ping.py'
    #sys.exit(signal)
    raise Exception('catcher: i am done')
signal.signal(signal.SIGBREAK, signal_handler)
subprocess.Popen('ping 10.192.225.219 -t')
##line = p1.stdout.readline()
##while line != '':
##    print line.strip()
##    line = p1.stdout.readline()
try:
    while True:
        print 'catcher:sleeping...'
        time.sleep(1)
except Exception as ex:
    print ex
    sys.exit(0)

