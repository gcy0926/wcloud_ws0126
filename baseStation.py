# -*- coding: utf8 -*-
#!/usr/bin/env python

import re
import httplib
import string
import random
import logging
import time
import ConfigParser, os
import ecode

def get(baseSec):
    """get baseStation key value."""
    c = ConfigParser.ConfigParser()
    items=[]
    try:
        if not c.read( os.path.join(os.getenv("CONFIG_DIR"),'baseStation.ini')):
            c.write(open(os.path.join(os.getenv("CONFIG_DIR"),'baseStation.ini'), "w"))
            raise
        
        if not c.has_section(baseSec):   #将文件baseStation.ini存为utf-8的
            raise
        tempitems = c.items(baseSec)   #得到群组（中科院）下，所有单位的基站键值对
        items=tempitems
    except:
        logging.exception('read baseStation file')

    return items   #format:   [(key,value),(key,value),...]       


#专用于获取群组地址
def get_org_addr(addrSec):
                
    """get org addr by addrSec."""
    c = ConfigParser.ConfigParser()
    try:
        if not c.read( os.path.join(os.getenv("CONFIG_DIR"),'baseStation.ini')):
            c.write(open(os.path.join(os.getenv("CONFIG_DIR"),'baseStation.ini'), "w"))
            raise
        if not c.has_section(addrSec):
            c.add_section(addrSec)
            c.write(open(os.path.join(os.getenv("CONFIG_DIR"),'baseStation.ini'), "w"))
            return ''
        else:
            tempitems = c.items(addrSec)
        logging.error('the tempitems for get org addr is : %s',tempitems)
            
    except:
        logging.exception('get org addr by addrSec')
        
    return tempitems
 
                
                 
