# -*- coding: utf8 -*-
#!/usr/bin/env python

import pymongo
import logging
import time
import ecode
import config
import json
from bson import json_util



client = pymongo.MongoClient(config.get('mongo_host'), config.get('mongo_port'))
db = client[config.get('mongo_db')]
contacts = db[config.get('mongo_contact_table')]


def init_db():
    contacts.drop()
    contacts.create_index([('uid',pymongo.ASCENDING)], unique=True)

def add_contact(uid,contact):
    if len(contact)<0:
        raise ecode.DATA_LEN_ERROR
    if list != type(contact):
        raise ecode.DATA_TYPE_ERROR
    if len(uid)<0:
         raise ecode.DATA_LEN_ERROR
    try:
        contacts.create_index([('uid',pymongo.ASCENDING)], unique=True)
        #是否含有uid项
        r = contacts.find_one({'uid':uid})
        if r :  #如果有则向contacts中追加
            for item in contact:
                #if not contacts.find({'contact.uid':item[1]}):
                u = contacts.update({'uid':uid},{'$addToSet':{'contact':item}}) 
            if u and u['n']:
                return True               
        else :
           if contacts.insert({'uid':uid,'contact':contact}):
               return True 
             
    except:
        logging.exception('add_contact failed. uid:%s', uid)
    raise ecode.DB_OP 

def del_contact(uid,contact):
    if len(contact)<0:
        raise ecode.DATA_LEN_ERROR
    if list != type(contact):
        raise ecode.DATA_TYPE_ERROR
    if len(uid)<0:
         raise ecode.DATA_LEN_ERROR
    try:
        #是否含有uid项
        r = contacts.find_one({'uid':uid})
        if r :  #如果有则从contact中删除
            for item in contact:
                #if not contacts.find({'contact.uid':item[1]}):
                u = contacts.update({'uid':uid},{'$pull':{'contact':item}})            
        if u and u['n']:
            return True
    except:
        logging.exception('del_contact failed. uid:%s', uid)
    raise ecode.DB_OP 

def get_contacts_by_uid(uid):
    if len(uid)<0:
        raise ecode.DATA_LEN_ERROR
    try:
        #是否含有uid项
        r = contacts.find_one({'uid':uid})
        
        return r['contact']
    except:
        logging.exception('get_contacts_by_uid failed. uid:%s', uid)
    raise ecode.DB_OP 
    