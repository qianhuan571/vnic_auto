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
import psutil

from ctypes import *
from win32gui import *
cfg = windll.cfgmgr32


devid_key = ''
devicelist = {}
strnum = 0
serlist = {}
sernum = 0
storeidlist = {}
storenum = 0

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

deviceClass = 'Net'
#deviceDesc = 'Intel(R) 82579LM Gigabit Network Connection'
deviceDesc = ' USB RNDIS'
##deviceId = 'USB\\VID_1366&PID_0105'
##deviceId = 'VEN_8086&DEV_1502'
deviceId = 'USB\\VID_1FC9&PID_0095'
#netcardmac = '00-12-13-10-15-11'
netcardmac = 'D4-BE-D9-45-22-60'
#netcardmac = '08-11-96-AB-D6-34'
pingtime = 0.2 #minites


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


#drivers = []
def get_dev_driver(devInst):
    global drivers
    buf = (c_wchar*1024)()
    blen = c_int(1024)
    cr = cfg.CM_Get_DevNode_Registry_PropertyW(devInst, CM_DRP_DRIVER, NULL, buf, byref(blen), 0);
    if cr == 0:
        #drivers.append(buf.value)
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
            #print 'No driver installed for the device'
            return 0
        return 1
    else:
        #print 'more than one same device are connected to host'
        return 2
    
def get_netcardip(mac):
    readflag = 0
    info = psutil.net_if_addrs()
    netcardlist = info.items()
    for i in range(len(netcardlist)):
        for j  in range (len(netcardlist[i][1])):
            if netcardlist[i][1][j][0]==-1 and netcardlist[i][1][j][1] == mac:
                return netcardlist[i][1][j+1][1]
    return 'the netcard hasn\'t installed'
                
                
taskkill = os.getenv('SYSTEMROOT')+'/System32/taskkill.exe'

def interact_run(cmd,timeout=2):
    def timeout_trigger(sub_process):
        #print 'timeout function trigger'
        os.system(taskkill+' /T /F /pid '+ str(sub_process.pid))
    fpinglog = open("pinglog.txt","w+")
    timeout = float(timeout)
    p = subprocess.Popen(cmd, 0, None, None, subprocess.PIPE, subprocess.PIPE,shell=True)
    t = threading.Timer(timeout*60, timeout_trigger, args=(p,))
    t.start()
    #p.wait()    
    p.poll()
    while p.returncode is None:
        line = p.stdout.readline()
        line = line.strip()
        p.poll()
        if line != '':
            fpinglog.write(line+'\n')
    fpinglog.close
    t.cancel()
    return p.returncode

dev_status =  device_is_installed(deviceId, deviceClass, deviceDesc)
if 1 == dev_status :
    netip = get_netcardip(netcardmac)
    print netip
    if netip != 'the netcard hasn\'t installed':
        ret = interact_run('ping -S '+ netip +' 10.192.225.219 -t',float(pingtime))
        pinglog=open("pinglog.txt",'r')
        log=pinglog.read()
        pinglog.close()
        SuccessRate = (float)(log.count('Reply from 10.192.225.219'))/(log.count('\n')-1)
        if ret == 1 and SuccessRate >= 0.97:
            FREEMV_INTERACT_RESULT = 0
            print 'run vnic pass'
        else:
            print 'run vnic fail'
elif 2 == dev_status:
    print 'more than one same device are connected to host'
elif 0 == dev_status:
    print 'no driver installed for the device'
else:
    print 'Device is not connected to host'
raw_input ('please press enter to exit')
