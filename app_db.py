# -*- coding: utf8 -*-
#!/usr/bin/env python


import pymongo
import logging
import time
import ecode
import config
import re


client = pymongo.MongoClient(config.get('mongo_host'), config.get('mongo_port'))
db = client[config.get('mongo_db')]
table = db[config.get('mongo_app_table')]


def init_db():
    table.drop()
    table.create_index([('app_id',pymongo.ASCENDING)], unique=True)


def is_has_app( app_id ):
    try:
        r = table.find_one({'app_id': app_id}, {'app_id':1})
        if r:
            return True
    except:
        logging.exception('is_has_app failed. app_id:%s', app_id)
        raise ecode.DB_OP
    return False

def make_webapp_id():
    import random
    for i in range(0,10):
        app_id = 'webapp.%d'%(random.randrange(10000000,99999999))
        if not is_has_app( app_id ):
            return app_id
    return 'webapp.00000000'


def add_app( app_id, app_name, apptype, version, versionCode, url, remark ):
    if len(app_id) <= 0:
        raise ecode.DATA_LEN_ERROR

    table.create_index([('app_id',pymongo.ASCENDING)], unique=True)

    if is_has_app( app_id):
        raise ecode.EXIST_APP

    try:
        if table.insert({'app_id':app_id
            , 'app_name':app_name
            , 'apptype':apptype
            , 'version': version
            , 'versionCode':versionCode
            , 'utime': str(int(time.time()))
            , 'url': url
            , 'remark': remark}):
            return True
    except:
        logging.exception('add new app failed. app_id:%s', app_id)
    raise ecode.DB_OP



def del_app( app_id):
    try:
        u = table.remove({'app_id':app_id})
        if u and u['n']:
            return True
    except:
        logging.exception('del_app failed. app_id:%s', app_id)
    raise ecode.DB_OP


def update( app_id, app_name, apptype, version, url, remark):
    try:
        u = table.update({'app_id':app_id}, {'$set':{
            'app_name':app_name
            , 'apptype':apptype
            , 'version': version
            , 'version': versionCode
            , 'utime': str(int(time.time()))
            , 'url':url
            , 'remark':remark}})
        if u and u['n']:
            return True
    except:
        logging.exception('update failed. app_id:%s', app_id)
    raise ecode.DB_OP


def get( app_id):
    r = None
    try:
        r = table.find_one({'app_id':app_id},{'_id':0})
    except:
        logging.exception('get failed. app_id:%s', app_id)
        raise ecode.DB_OP
    if not r:
        raise ecode.NOT_EXIST_APP
    return r

def getapp( app_id,versionCode):
    r = None
    try:
        r = table.find_one({'app_id':app_id,'versionCode':versionCode},{'_id':0,'app_id':1,'versionCode':1,'url':1})
    except:
        logging.exception('get failed. app_id:%s', app_id)
        raise ecode.DB_OP
    if not r:
        raise ecode.NOT_EXIST_APP
    return r


def get_app_list( key='', sortkey='utime', asc=1, start=0, count=100):
    try:
        al = []
        if key:
            rexExp = re.compile('.*%s.*'%(key), re.IGNORECASE)
            r = table.find({'app_name':rexExp}
                    , {'_id':0,'app_id':1,'app_name':1,'utime':1})
        else:
            r = table.find({}, {'_id':0,'app_id':1,'app_name':1,'utime':1})
        
        for item in r.sort([(sortkey,asc)]).skip(start).limit(count):
            logging.error("获得的应用信息%s",str(item) )
            al.append( item['app_id'] )
        return al

    except:
        logging.exception('get app list failed.')
    raise ecode.DB_OP


def get_apps_list( key='', sortkey='utime', asc=1, start=0, count=100):
    try:
        al = []
        if key:
            rexExp = re.compile('.*%s.*'%(key), re.IGNORECASE)
            r = table.find({'app_name':rexExp}
                    , {'_id':0,'app_id':1,'app_name':1,'utime':1})
        else:
#             r = table.find({}, {'_id':0,'app_id':1,'app_name':1,'utime':1})
            r = table.find({}, {'_id':0,'app_id':1,'versionCode':1})

        for item in r.sort([(sortkey,asc)]).skip(start).limit(count):
            al.append( item )
        return al

    except:
        logging.exception('get app list failed.')
    raise ecode.DB_OP






