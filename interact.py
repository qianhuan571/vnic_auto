#--*-- coding:utf8 --*--
import os
import sys
import string
import datetime
import math
import _winreg
#import win32con
#import win32gui
#import msvcrt
import serial
import time
import threading
import subprocess
import signal
import psutil
import hashlib

from shutil import *
from ctypes import *
from win32gui import *
cfg = windll.cfgmgr32


#参数设定：
deviceClass = 'Net'
deviceDesc = 'NXP USB RNDIS' 
deviceId = 'USB\\VID_1FC9&PID_0095'
netCardMac = '00-12-13-10-15-11' 

# deviceDesc = 'Intel(R) Dual Band Wireless-AC 8265' #待测USB网卡描述符
# deviceId = 'VEN_8086&DEV_24FD' #待测USB网卡ID
# netCardMac = '90-61-AE-4A-BB-27' #待测USB网卡Mac

pingCount =  5 #ping的次数


RERVALS = {
        0x00000000:"CR_SUCCESS",
        0x00000001:"CR_DEFAULT",
        0x00000002:"CR_OUT_OF_MEMORY",
        0x00000003:"CR_INVALID_POINTER",
        0x00000004:"CR_INVALID_FLAG",
        0x00000005:"CR_INVALID_DEVNODE",
        0x00000006:"CR_INVALID_RES_DES",
        0x00000007:"CR_INVALID_LOG_CONF",
        0x00000008:"CR_INVALID_ARBITRATOR",
        0x00000009:"CR_INVALID_NODELIST",
        0x0000000A:"CR_DEVNODE_HAS_REQS",
        0x0000000B:"CR_INVALID_RESOURCEID",
        0x0000000C:"CR_DLVXD_NOT_FOUND",   
        0x0000000D:"CR_NO_SUCH_DEVNODE",
        0x0000000E:"CR_NO_MORE_LOG_CONF",
        0x0000000F:"CR_NO_MORE_RES_DES",
        0x00000010:"CR_ALREADY_SUCH_DEVNODE",
        0x00000011:"CR_INVALID_RANGE_LIST",
        0x00000012:"CR_INVALID_RANGE",
        0x00000013:"CR_FAILURE",
        0x00000014:"CR_NO_SUCH_LOGICAL_DEV",
        0x00000015:"CR_CREATE_BLOCKED",
        0x00000016:"CR_NOT_SYSTEM_VM",   
        0x00000017:"CR_REMOVE_VETOED",
        0x00000018:"CR_APM_VETOED",
        0x00000019:"CR_INVALID_LOAD_TYPE",
        0x0000001A:"CR_BUFFER_SMALL",
        0x0000001B:"CR_NO_ARBITRATOR",
        0x0000001C:"CR_NO_REGISTRY_HANDLE",
        0x0000001D:"CR_REGISTRY_ERROR",
        0x0000001E:"CR_INVALID_DEVICE_ID",
        0x0000001F:"CR_INVALID_DATA",
        0x00000020:"CR_INVALID_API",
        0x00000021:"CR_DEVLOADER_NOT_READY",
        0x00000022:"CR_NEED_RESTART",
        0x00000023:"CR_NO_MORE_HW_PROFILES",
        0x00000024:"CR_DEVICE_NOT_THERE",
        0x00000025:"CR_NO_SUCH_VALUE",
        0x00000026:"CR_WRONG_TYPE",
        0x00000027:"CR_INVALID_PRIORITY",
        0x00000028:"CR_NOT_DISABLEABLE",
        0x00000029:"CR_FREE_RESOURCES",
        0x0000002A:"CR_QUERY_VETOED",
        0x0000002B:"CR_CANT_SHARE_IRQ",
        0x0000002C:"CR_NO_DEPENDENT",
        0x0000002D:"CR_SAME_RESOURCES",
        0x0000002E:"CR_NO_SUCH_REGISTRY_KEY",
        0x0000002F:"CR_INVALID_MACHINENAME",   
        0x00000030:"CR_REMOTE_COMM_FAILURE",   
        0x00000031:"CR_MACHINE_UNAVAILABLE",   
        0x00000032:"CR_NO_CM_SERVICES",   
        0x00000033:"CR_ACCESS_DENIED",   
        0x00000034:"CR_CALL_NOT_IMPLEMENTED",
        0x00000035:"CR_INVALID_PROPERTY",
        0x00000036:"CR_DEVICE_INTERFACE_ACTIVE",
        0x00000037:"CR_NO_SUCH_DEVICE_INTERFACE",
        0x00000038:"CR_INVALID_REFERENCE_STRING",
        0x00000039:"CR_INVALID_CONFLICT_LIST",
        0x0000003A:"CR_INVALID_INDEX",
        0x0000003B:"CR_INVALID_STRUCTURE_SIZE",
        0x0000003C:"NUM_CR_RESULTS"
    }


CM_DRP_DEVICEDESC = 0x0001
CM_DRP_CLASS = 0x0008
CM_DRP_DRIVER = 0x000A
NULL = 0


def get_dev_class(devInst):
    buf = (c_wchar*1024)()
    blen = c_int(1024)
    cr = cfg.CM_Get_DevNode_Registry_PropertyW(devInst, CM_DRP_CLASS, NULL, buf, byref(blen), 0)
    if cr == 0:
        return buf.value
    else:
        return "ERR(%d):%s"%(devInst, RERVALS[cr])
    
def get_dev_desc(devInst):
    buf = (c_wchar*1024)()
    blen = c_int(1024)
    cr = cfg.CM_Get_DevNode_Registry_PropertyW(devInst, CM_DRP_DEVICEDESC, NULL, buf, byref(blen), 0)
    if cr == 0:
        return buf.value
    else:
        return "ERR(%d):%s"%(devInst, RERVALS[cr])


def get_dev_id(devInst):
    buf = (c_wchar*1024)()
    blen = c_int(1024)
    cr = cfg.CM_Get_Device_IDW(devInst, buf, byref(blen), 0)
    if cr == 0:
        return buf.value
    else:
        return "ERR(%d):%s"%(devInst, RERVALS[cr])


def get_dev_driver(devInst):
    global drivers
    buf = (c_wchar*1024)()
    blen = c_int(1024)
    cr = cfg.CM_Get_DevNode_Registry_PropertyW(devInst, CM_DRP_DRIVER, NULL, buf, byref(blen), 0);
    if cr == 0:
        return buf.value
    else:
        return "ERR(%d):%s"%(devInst, RERVALS[cr])


def target_dev(tarDevId, tarClass, tarDesc):
    def dev_child(nodeInst, deviceList, targetDevId, targetClass, targetDesc):
        devParent = c_int(nodeInst)
        devChild = c_int(0)
        devNextChild = c_int(0)
        if cfg.CM_Get_Child(byref(devChild), devParent, 0) == 0:
            desc = get_dev_desc(devChild.value)
            devId = get_dev_id(devChild.value)
            clas = get_dev_class(devChild.value)
            driver = get_dev_driver(devChild.value)
            if tarDevId in devId and tarClass in clas and tarDesc in desc:
                node = {}
                node.update({"DevInst":str(devChild.value)})
                node.update({"Desc":desc})
                node.update({"DevId":devId})
                node.update({"Class":clas})
                node.update({"Driver":driver})
                deviceList.append(node)
            dev_child(devChild.value, deviceList, targetDevId, targetClass, targetDesc)
            while cfg.CM_Get_Sibling(byref(devNextChild), devChild, 0) == 0:
                devChild.value = devNextChild.value
                desc = get_dev_desc(devChild.value)
                devId = get_dev_id(devChild.value)
                clas = get_dev_class(devChild.value)
                driver = get_dev_driver(devChild.value)
                if tarDevId in devId and tarClass in clas and tarDesc in desc:
                    node = {}
                    node.update({"DevInst":str(devChild.value)})
                    node.update({"Desc":desc})
                    node.update({"DevId":devId})
                    node.update({"Class":clas})
                    node.update({"Driver":driver})
                    deviceList.append(node)
                dev_child(devChild.value, deviceList, targetDevId, targetClass, targetDesc)

    devlist = []
    rootdev = []
    devInst = c_int(0)
    devInstNext = c_int(0)
    if 0 == cfg.CM_Locate_DevNodeW(byref(devInst), 0, 0):
        desc = get_dev_desc(devInst.value)
        devId = get_dev_id(devInst.value)
        clas = get_dev_class(devInst.value)
        driver = get_dev_driver(devInst.value)
        rootdev.append(devInst)
        if tarDevId in devId and tarClass in clas and tarDesc in desc:
            node = {}
            node.update({"DevInst":str(devInst.value)})
            node.update({"Desc":desc})
            node.update({"DevId":devId})
            node.update({"Class":clas})
            node.update({"Driver":driver})
            devlist.append(node)
        while 0 == cfg.CM_Get_Sibling(byref(devInstNext), devInst, 0):
            devInst.value = devInstNext.value
            desc = get_dev_desc(devInst.value)
            devId = get_dev_id(devInst.value)
            driver = get_dev_driver(devInst.value)
            rootdev.append(devInst)
            if tarDevId in devId and tarClass in clas and tarDesc in desc:
                node = {}
                node.update({"DevInst":str(devInst.value)})
                node.update({"Desc":desc})
                node.update({"DevId":devId})
                node.update({"Class":clas})
                node.update({"Driver":driver})
                devlist.append(node)
    for node in rootdev:
        dev_child(node.value, devlist, tarDevId, tarClass, tarDesc)
    return devlist

import time

def device_is_installed(tarDevId, tarClass, tarDesc):
    devList = target_dev(tarDevId, tarClass, tarDesc)
    if 0 == len(devList):
        #print 'Device is not connected to host'
        return -1
    elif 1 == len(devList):
        driver = get_dev_driver(int(devList[0]['DevInst']))
        if 'ERR' in driver:
            print 'No driver installed for the device'
            return -2
        return 0
    else:
        #print 'more than one same device are connected to host'
        return 1
    
def get_netcardip(mac):
    readflag = 0
    info = psutil.net_if_addrs()
    netcardlist = info.items()
    for i in range(len(netcardlist)):
        for j  in range (len(netcardlist[i][1])):
            if netcardlist[i][1][j][0]==-1 and netcardlist[i][1][j][1] == mac:
                return netcardlist[i][1][j+1][1]
    return -1
                

import time
def interact_run(netIp,pinglogfile,pingcount):
    fPingLog = open(pinglogfile ,"w+")
    p = subprocess.Popen('ping 192.168.1.1 -t -S '+netIp,stdout=subprocess.PIPE,stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    count = pingcount
    p.poll()
    line = p.stdout.readline()
    while line != '' or p.returncode == None:
        try:
            line = line.strip()
            if line != '':
                fPingLog.write(line+'\n')
                print line   
        except IOError:
            break
        time.sleep(1)
        if count == 0:
            p.terminate()
        count = count - 1
        p.poll()
        line = p.stdout.readline()
    fPingLog.close()
    return p.returncode

def ping_loss(pinglog):
    sum = 0
    count = 0
    logfile=open(pinglog, 'r')
    line=logfile.readline()
    while '' != line:
        if "time=" in line:
            count = count + 1
        sum = sum + 1
        line=logfile.readline()
    if sum != 0:
        lossrate = 100 - count*100 / (sum-1)
    else:
        return -1
    print "lossrate:"+str(lossrate)
    return lossrate

def analyze_result(pinglog):
    lossrate = ping_loss(pinglog)
    if lossrate == -1:
        result = -5
        print 'no ping log'
    elif lossrate <= 5:
        result = 0
        print 'the dev_vnic case pass'
    else :
        result = -4
        print 'the dev_vnic case fail: high data package loss rate'
    return result

def main(deviceid, deviceclass, devicedesc, netcardmac, pinglogfile, pingcount):
    dev_status =  device_is_installed(deviceid, deviceclass, devicedesc)
    if 0 == dev_status :
        netip = get_netcardip(netcardmac)
        if netip != 'the netcard hasn\'t installed':
            print 'the netcard ip:'+ netip
            ret = interact_run(netip,pinglogfile,pingcount)
            if 1 == ret:
                result = analyze_result(pinglogfile)
            else:
                result = -3
                print 'the subprocess encounter unknown problem, please retry.'
        else:
            result = -4
            print netip
    elif 1 == dev_status:
        result = 1
        print 'more than one same device are connected to host'
    elif -2 == dev_status:
        result = -2
        print 'no driver installed for the device'
    elif -1 == dev_status:
        result = -1
        print 'Device is not connected to host'
    return result

    
time.sleep(8)
FREEMV_INTERACT_RESULT = main(deviceId, deviceClass, deviceDesc, netCardMac, 'pinglog.txt', pingCount)
time.sleep(2)
#print FREEMV_INTERACT_RESULT
#raw_input ('please press enter to exit')
    
