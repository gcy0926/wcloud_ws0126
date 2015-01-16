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

def get(sct,time1='',time2=''):
    """get trace key value."""
    """ 传入的时间为时间戳"""
    c = ConfigParser.ConfigParser()
    items=[]
    try:
        if not c.read( os.path.join(os.getenv("CONFIG_DIR"),'trace.ini')):
            c.write(open(os.path.join(os.getenv("CONFIG_DIR"),'trace.ini'), "w"))
            raise
        if not c.has_section(sct):
            raise
        tempitems = c.items(sct)
        if time1=='' and time2=='': #如果时间都为空，则是获取全部的键值对
#             for item in tempitems:
#                 items.append({item[0]:item[1]});
            items=tempitems
        elif time1==''and time2!='':   #如果起始时间为空，则获取截止日期之前的所有值
            for item in tempitems:
                if str(item[0])<str(time2):
#                     items[item[0]]=c.get(sct,item[0])
                     items.append(item)
        elif time1!='' and time2=='':
            for item in tempitems:
                if str(item[0])>str(time1):
#                     items[[item[0]]]=c.get(sct,item[0])
                    items.append(item)
        else:
            for item in tempitems:
                if str(item[0])>str(time1) and str(item[0])<str(time2):
#                     items[[item[0]]]=c.get(sct,item[0])
                    items.append(item)
    except:
         logging.exception('read trace file')

    return items      


def set(sct,option,value):
    c = ConfigParser.ConfigParser()
    try:
#         if os.path.exists(os.path.join(os.getenv("CONFIG_DIR"),'trace.ini')):
        if not c.read( os.path.join(os.getenv("CONFIG_DIR"),'trace.ini')):
            c.write(open(os.path.join(os.getenv("CONFIG_DIR"),'trace.ini'), "w"))
            raise
#         else 
        if not c.has_section(sct):  #如果section不存在则新添加一个并添加新的一项
            c.add_section(sct)
        items = c.items(sct)
        oldtime = 0.0
        if len(items)>0:
        #第一条记录的时间    时间戳是秒数
            oldtime = items[0][0]           
            if (float(option)-float(oldtime))>= 2*24*60*60:  #只存储两天的信息
                c.remove_option(sct,items[0][0])  #如果存储的数据超过两天则删除最早的一条记录，然后插入新纪录
        c.set(sct,str(option),value)
        c.write(open(os.path.join(os.getenv("CONFIG_DIR"),'trace.ini'), "w"))
    except:
        logging.exception('read trace file')
        
    return True

def get_last_option(sct):
                
    """get sct last key value."""
    c = ConfigParser.ConfigParser()
    items={}
    try:
        if not c.read( os.path.join(os.getenv("CONFIG_DIR"),'trace.ini')):
            c.write(open(os.path.join(os.getenv("CONFIG_DIR"),'trace.ini'), "w"))
            raise
        if not c.has_section(sct):
           c.add_section(sct)
           c.write(open(os.path.join(os.getenv("CONFIG_DIR"),'trace.ini'), "w"))
           return []
        else:
            tempitems = c.items(sct)
            k = len(tempitems)
            if k <=0:
                return []
            else:
                return tempitems[k-1]
    except:
         logging.exception('get last_option file')
 
                
                 
            
       
        
    
    