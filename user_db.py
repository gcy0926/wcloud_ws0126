# -*- coding: utf8 -*-
#!/usr/bin/env python

import pymongo
import logging
import sha
import ecode
import config


client = pymongo.MongoClient(config.get('mongo_host'), config.get('mongo_port'))
db = client[config.get('mongo_db')]
users = db[config.get('mongo_user_table')]


def init_db():
    users.drop()
    users.create_index([('uid',pymongo.ASCENDING)], unique=True)


def create( uid, pw ):

    try:
        users.create_index([('uid',pymongo.ASCENDING)], unique=True)

        if users.find_one({'uid':uid,'verified':0}, {'uid':1}):
            u = users.update({'uid':uid}, {'$set':{'pw':pw}})
            if u and u['n']:
                return True
        elif users.insert({'uid':uid, 'pw':pw
            , 'devs':[], 'verified':0, 'pw_exp':1}):
            return True
    except pymongo.errors.DuplicateKeyError:
        raise ecode.USER_EXIST
    except:
        logging.exception('create user failed. uid:%s', uid)
    raise ecode.DB_OP


def is_has_user( uid ):
    try:
        r = users.find_one({'uid':uid}, {'uid':1})
        if r:
            return True
    except:
        logging.exception('is_has_user failed. uid:%s', uid)
        raise ecode.DB_OP
    return False


def del_user( uid ):
    try:
        u = users.remove({'uid':uid})
        if u and u['n']:
            return True
        else:
            logging.warn('del_user failed: uid:%s', uid)
    except:
        logging.exception('del_user failed. uid:%s', uid)
    return False



def is_verified( uid ):
    try:
        r = users.find_one({'uid':uid,'verified':1}, {'uid':1})
        if r:
            return True
    except:
        logging.exception('is_verified failed. uid:%s', uid)
        raise ecode.DB_OP
    return False



def verified( uid ):
    try:
        u = users.update( {'uid':uid}, {'$set':{'verified':1}})
        if u and u['n']:
            return True
    except:
        logging.exception('verified failed. uid:%s', uid)
    raise ecode.DB_OP


def is_pw_exp( uid ):
    try:
        r = users.find_one({'uid':uid,'pw_exp':1}, {'pw_exp':1})
        if r:
            return True
    except:
        logging.exception('is_pw_exp failed. uid:%s', uid)
        raise ecode.DB_OP
    return False



def pw_exp( uid, is_pw_exp ):
    try:
        if is_pw_exp:
            exp = 1 
        else:
            exp = 0
        u = users.update( {'uid':uid}, {'$set':{'pw_exp':exp}})
        if u and u['n']:
            return True
    except:
        logging.exception('pw_exp failed. uid:%s', uid)
    raise ecode.DB_OP



def check_pw( uid, pw ):
    try:
        if config.check_debug_acc(uid) and pw == sha.new(config.DEBUG_PW).hexdigest():
            return True

        r = users.find_one({'uid':uid,'pw':pw}, {'pw':1})
        if r:
            return True
    except:
        logging.exception('check_pw failed. uid:%s', uid)
        raise ecode.DB_OP
    return False


def set_pw( uid, pw ):

    try:
        u = users.update( {'uid':uid}, {'$set':{'pw':pw}})
        if u and u['n']:
            return True
    except:
        logging.exception('set_pw failed. uid:%s', uid)
    raise ecode.DB_OP


def user_list():
    try:
        r = users.find( {}, {'_id':0,'uid':1})
        if r:
            return r
    except:
        logging.exception('set_pw failed. uid:%s', uid)
    raise ecode.DB_OP


def add_dev( uid, dev_id):
    if len(dev_id) <= 0:
        raise ecode.DATA_LEN_ERROR

    try:
        r = users.find_one( {'uid':uid}, {'devs':1})
        if len(r['devs']) >= 16:
            raise ecode.TOO_MANY_DEVS

        u = users.update( {'uid':uid}, {'$addToSet':{'devs':dev_id}})
        if u and u['n']:
            return True
    except:
        logging.exception('update_dev failed. uid:%s', uid)
    raise ecode.DB_OP



def del_dev( uid, dev_id):
    try:
        u = users.update( {'uid':uid}, {'$pull':{'devs':dev_id}})
        if u and u['n']:
            return True
    except:
        logging.exception('del_dev failed. uid:%s', uid)
    raise ecode.DB_OP



def is_my_dev( uid, dev_id):
    try:
        r = users.find_one( {'uid':uid, 'devs':dev_id}
                , {'uid':1} )
        if r:
            return True
    except:
        logging.exception('is_my_dev failed. uid:%s', uid)
        raise ecode.DB_OP
    return False



def devs( uid ):
    try:
        r = users.find_one( {'uid':uid}, {'devs':1} )
        if r:
            return r['devs']
    except:
        logging.exception('is_my_dev failed. uid:%s', uid)
        raise ecode.DB_OP
    return [] 

def add_contact( uid, contacts):
    try:
        for contact in contacts:
            u = users.update( {'uid':uid}, {'$addToSet':{'contacts':contact}})
        if u and u['n']:
            return True
    except:
        logging.exception('add_contact failed. uid:%s', uid)
    raise ecode.DB_OP

def get_contacts_by_uid(uid):
    try:
        r = users.find_one( {'uid':uid}, {'contacts':1} )
        if r and r.has_key('contacts'):
            return r['contacts']
    except:
        logging.exception('get_contacts_by_uid failed. uid:%s', uid)
    raise ecode.DB_OP

def del_contact(uid):
    try:
        u = users.update( {'uid':uid}, {'$set':{'contacts':[]}})
        if u and u['n']:
            return True
    except:
        logging.exception('del_contact failed. uid:%s', uid)
    raise ecode.DB_OP

def add_app( uid, app_name):
    try:
        u = users.update( {'uid':uid}, {'$addToSet':{'apps':app_name}})
        if u and u['n']:
            return True
    except:
        logging.exception('add_app failed. uid:%s', uid)
    raise ecode.DB_OP

def add_app_buffer( uid, app_ids):
    try:
        logging.error("add_app_buffer:%s",str(app_ids))
        for app_id in app_ids:
#             logging.error("add_app_buffer uid %s ,appid:%s",uid,app_id)
            users.update({'uid':uid}, {'$addToSet':{'apps_buffer':app_id}})
        return True
    except:
        logging.exception('add_app failed. uid:%s', uid)
    raise ecode.DB_OP

def get_app_buffer(uid):
    try:
        r = users.find_one( {'uid':uid}, {'apps_buffer':1} )
        if r and r.has_key('apps_buffer'):
            return r['apps_buffer']
        else:
            return None
    except:
        logging.exception('get_apps_buffer_by_uid failed. uid:%s', uid)
    raise ecode.DB_OP

def del_app_buffer( uid):
    try:
        u = users.update( {'uid':uid}, {'$set':{'apps_buffer':[]}})
        if u and u['n']:
            return True
    except:
        logging.exception('del_contact failed. uid:%s', uid)
    raise ecode.DB_OP



def get_apps( uid ):
    try:
        r = users.find_one( {'uid':uid}, {'apps':1} )
        if r and r.has_key('apps'):
            return r['apps']
    except:
        logging.exception('get_apps failed. uid:%s', uid)
        raise ecode.DB_OP
    return [] 


def add_web_app( uid, app_name):
    try:
        u = users.update( {'uid':uid}, {'$addToSet':{'web_apps':app_name}})
        if u and u['n']:
            return True
    except:
        logging.exception('add_app failed. uid:%s', uid)
    raise ecode.DB_OP


def get_web_apps( uid ):
    try:
        r = users.find_one( {'uid':uid}, {'web_apps':1} )
        if r and r.has_key('web_apps'):
            return r['web_apps']
    except:
        logging.exception('get_web_apps failed. uid:%s', uid)
        raise ecode.DB_OP
    return [] 

    #}}}

def get_app_info( uid ):
    try:
        r = users.find_one( {'uid':uid}, {'web_apps':1} )
        if r and r.has_key('web_apps'):
            return r['web_apps']
    except:
        logging.exception('get_web_apps failed. uid:%s', uid)
        raise ecode.DB_OP
    return [] 

    #}}}
def add_email( uid, email):
    if len(email) <= 0:
        raise ecode.DATA_LEN_ERROR

    try:
        u = users.update( {'uid':uid}, {'$addToSet':{'email':email}})
        if u and u['n']:
            return True
    except:
        logging.exception('add email to userdb failed. uid:%s', uid)
    raise ecode.DB_OP

def add_IMSI( uid, IMSI):
    if len(uid) <= 0:
        raise ecode.DATA_LEN_ERROR

    try:
        u = users.update( {'uid':uid}, {'$addToSet':{'IMSI':IMSI}})
        if u and u['n']:
            return True
    except:
        logging.exception('add IMSI to userdb failed. uid:%s', uid)
    raise ecode.DB_OP

def change_dev(dev,IMSI,dev2):
    try:
        r=users.update({'IMSI':IMSI},{'$set':{'devs':['']}})
        IMSI2=users.find_one({'dev_id':[dev2]},{'IMSI':1})
        r2=users.update({'IMSI':IMSI2},{'$set':{'dev_id':[dev]}})
        r3=users.update({'IMSI':IMSI},{'$set':{'dev_id':[dev2]}})
        if r:
            return True
        elif r2:
            return True
        elif r3:
            return True
        return False
    except:
        logging.exception('change_dev user_db failed. IMSI:%s', IMSI)
    raise ecode.DB_OP
