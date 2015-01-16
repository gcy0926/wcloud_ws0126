# -*- coding: utf8 -*-
#!/usr/bin/env python


import sys
import commands
import re
import zipfile
import base64
import os
import logging

aapt_cmd = '/home/wcloud/android/aapt'

def get_apk_info( apk ):
    apkinfo = {
            'app_id':'',
            'app_name':'',
            'version':'',
            'icon':'',
            'versionCode':''
            }

    rt = commands.getstatusoutput( '%s d badging "%s"'%(aapt_cmd, apk))
    logging.error('get apk info by aapt, rt=%d, output=%s', rt[0], rt[1])
    if not rt[0]:
        logging.error('get apk info by aapt, rt=%d, output=%s', rt[0], rt[1])
    rt = rt[1]

    m = re.findall( r"^package: name='(?P<app_id>\S*)'", rt, re.M|re.S) 
    if m:
        apkinfo['app_id'] = m[0]

    m = re.findall( r"^package:[^\n]*versionName='(?P<version>\S*)'", rt, re.M|re.S) 
    if m:
        apkinfo['version'] = m[0]
        
    m = re.findall( r"^package:[^\n]*versionCode='(?P<versionCode>\S*)'", rt, re.M|re.S) 
    if m:
        apkinfo['versionCode'] = m[0]

#     m = re.findall( r"^locales:\s'[^\n]*'\s'(?P<locales>\S*)'", rt, re.M|re.S) 
#     if m:
    m = re.findall( r"^application: label='(?P<app_name>\S*)'"
                , rt, re.M|re.S) 
    if m:
        apkinfo['app_name'] = m[0]

    if not apkinfo['app_name']:
        m = re.findall( r"^application-label:'(?P<app_name>[^\n]*)'", rt, re.M|re.S) 
        if m:
            apkinfo['app_name'] = m[0]

    m = re.findall( r"^application: \S*\s*icon='(?P<icon_path>[^\n]*)'", rt, re.M|re.S) 
    if m:
        with zipfile.ZipFile(apk,'r') as apk_file:
            apkinfo['icon'] = base64.standard_b64encode(apk_file.read(m[0]))
    
    logging.error(' apkinfo%s', apkinfo)

    return apkinfo


