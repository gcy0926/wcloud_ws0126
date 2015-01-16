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
ads = db[config.get('mongo_admin_table')]


def init_db():
    ads.drop()
    ads.create_index([('uid',pymongo.ASCENDING)], unique=True)

def add_admin(uid,pw,ou):
        
    try:
        ads.create_index([('uid',pymongo.ASCENDING)], unique=True)

        if ads.find_one({'uid':uid}):
            u = ads.update({'uid':uid}, {'$set':{'pw':pw,'ou':ou}})
            if u and u['n']:
                return True
        elif ads.insert({'uid':uid, 'pw':pw, 'ou':ou}):
            return True
    except pymongo.errors.DuplicateKeyError:
        raise ecode.USER_EXIST
    except:
        logging.exception('create admin failed. uid:%s', uid)
    raise ecode.DB_OP

def get_user_list():
    
    try:
        r = ads.find({},{'_id':0,'uid':1})
        if r:
            return r
    except:
        logging.exception('get_user_list failed')
    raise ecode.DB_OP

def is_has_admin(uid):
    try:
        r = ads.find_one({'uid':uid}, {'uid':1})
        if r:
            return True
    except:
        logging.exception('is_has_admin failed. uid:%s', uid)
        raise ecode.DB_OP
    return False

def check_pw( uid, pw ):
    try:
        #if config.check_debug_acc(uid) and pw == sha.new(config.DEBUG_PW).hexdigest():
           # return True

        r = ads.find_one({'uid':uid,'pw':pw}, {'pw':1})
        if r:
            return True
    except:
        logging.exception('check_pw failed. uid:%s', uid)
        raise ecode.DB_OP
    return False
 
def get_ou_by_uid( uid):
    try:

        r = ads.find_one({'uid':uid}, {'ou':1})
        if r and r.has_key('ou'):
            return r['ou']
    except:
        logging.exception('get_ou_by_uid failed. uid:%s', uid)
        raise ecode.DB_OP 
    return '' 
 
def get_pw_by_uid(uid):
    try:
        r = ads.find_one({'uid':uid}, {'pw':1})
        if r and r.has_key('pw'):
            return r['pw']
    except:
        logging.exception('get_pw_by_uid failed. uid:%s', uid)
        raise ecode.DB_OP 
    return '' 

def update_pw(uid,pw):
    try:
        
        u = ads.update({'uid':uid}, {'$set':{'pw':pw}})
        if u and u['n']:
            return True
    except:
        logging.exception('get_pw_by_uid failed. uid:%s', uid)
        raise ecode.DB_OP 
    return False     
        
def get_ou_and_email_by_uid( uid):
    try:

        r = ads.find_one({'uid':uid}, {'ou':1,'email':1})
        ou = ''
        email = ''
        if r and r.has_key('ou'):
            ou = r['ou']
        if r and r.has_key('email'):
            email = r['email']
    except:
        logging.exception('get_ou_by_uid failed. uid:%s', uid)
        raise ecode.DB_OP 
    return ou,email  
    
