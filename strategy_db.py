# -*- coding: utf8 -*-
#!/usr/bin/env python

import pymongo
import logging
import time
import ecode
import config
import json
import re
from bson import json_util



client = pymongo.MongoClient(config.get('mongo_host'), config.get('mongo_port'))
db = client[config.get('mongo_db')]
strategys = db[config.get('mongo_strategy_table')]


def init_db():
    strategys.drop()
    strategys.create_index([('strategy_id',pymongo.ASCENDING)], unique=True)


def new_strategy( strategy,users,userdesc):
    if dict != type(strategy):
        raise ecode.DATA_TYPE_ERROR
    if len(strategy) <= 0:
        raise ecode.DATA_LEN_ERROR
    logging.error(strategy)
    logging.error(len(strategy))
    if len(strategy) > 14:
        raise ecode.DATA_LEN_ERROR
    strategy_id = strategy['strategy_id']
    start = strategy['start']
    end = strategy['end']
    lon = strategy['lon']
    lat = strategy['lat']
    desc = strategy['desc']
    radius = strategy['radius']
    wifi = strategy['wifi']
    bluetooth = strategy['bluetooth']
 #   camera = strategy['camera']
    tape = strategy['tape']
 #   data_work = strategy['data_work']
    baseStationID = strategy['baseStationID']
    
    if len(strategy_id) <= 0:
        raise ecode.DATA_LEN_ERROR
    try:
        strategys.create_index([('strategy_id',pymongo.ASCENDING)], unique=True)
        if strategys.insert({'strategy_id':strategy_id, 'start':start,'end':end,'lon':lon, 'lat':lat,'radius':radius,'desc':desc,'wifi':wifi,'bluetooth':bluetooth,'tape':tape,'users':users,'userdesc':userdesc,'baseStationId':baseStationID}):
            return True
    except:
        logging.exception('add new strategy failed. strategy_id:%s', strategy_id)
    raise ecode.DB_OP


def get_strategy_by_id( strategy_id):
    try:
        r = strategys.find_one({'strategy_id':strategy_id},{"_id" : 0})
        strategy = r
        return strategy
    except:
        logging.exception('get_strategy_by_id failed. strategy_id:%s', strategy_id)
    raise ecode.DB_OP

def get_strategy_by_id1( strategy_id):
    try:
        r = strategys.find_one({'strategy_id':strategy_id},{"_id" : 0,'users':0,'userdesc':0})
        strategy = r
        return strategy
    except:
        logging.exception('get_strategy_by_id failed. strategy_id:%s', strategy_id)
    raise ecode.DB_OP

def get_strategys():
    try:
        r = strategys.find({},{"_id" : 0})
        strs = []
        for doc in r:
            #strategy = json.dumps(doc, default=json_util.default)
            strs.append(doc)
        return strs
    except:
        logging.exception('get_strategts failed.')
    raise ecode.DB_OP

def get_strategys_by_admin(ou):
    try:
        #str = MongoRegex("/".ou.".*/i")  利用正则表达式来完成模糊查找
        str = re.compile(r'.*'+ou+'.*')
        r = strategys.find({"userdesc.name":{'$regex':str}},{"_id" : 0})
        strs = []
        for doc in r:
            #strategy = json.dumps(doc, default=json_util.default)
            strs.append(doc)
        return strs
    except:
        logging.exception('get_strategts failed.')
    raise ecode.DB_OP

#客户端调用的get_strategys()
def get_strategys_to_user(ids):
    try:
        user_strategys = []
        for id in ids: 
#             logging.exception(id)
            strategy_id = str(id['strategy_id'])
            r = strategys.find_one({'strategy_id':strategy_id},{"_id" : 0,'users':0,'userdesc':0})
#         strategy = r
            if r:
                stra = r
                user_strategys.append(stra)
        return user_strategys
    except:
        logging.exception('get_strategts_to_user failed.')
    raise ecode.DB_OP

def get_strategys_of_user_by_admin(ids):
    try:
        user_strategys = []
        for id in ids: 
#             logging.exception(id)
            strategy_id = str(id['strategy_id'])
            r = strategys.find_one({'strategy_id':strategy_id},{"_id" : 0,'users':0,'userdesc':0})
#         strategy = r
            if r:
                stra = r
                stra['is_read']=str(id['is_read'])
                user_strategys.append(stra)
        return user_strategys
    except:
        logging.exception('get_strategts_to_user failed.')
    raise ecode.DB_OP
        
def mod_strategy( strategy, users, userdesc ):
    strategy_id = strategy['strategy_id']
    try:
        u = strategys.update({'strategy_id':strategy_id}
                , {'$set':{'start':strategy['start'],'end':strategy['end']
                ,'lon':strategy['lon']
                ,'lat':strategy['lat']
                ,'desc':strategy['desc']
                ,'radius':strategy['radius']
                ,'wifi':strategy['wifi']
                ,'bluetooth':strategy['bluetooth']
               # ,'camera':strategy['camera']
                ,'tape':strategy['tape']
               # ,'data_work':strategy['data_work']
                ,'users':users
                ,'userdesc':userdesc
                ,'baseStationId':strategy['baseStationID']}})
        if u and u['n']:
            return True
    except:
        logging.exception('mod_strategy failed. strategy_id:%s', strategy_id)
        raise ecode.DB_OP
    return False

def mod_users_of_strategy(strategy_id,users,userdesc):
    try:
        u = strategys.update({'strategy_id':strategy_id}
                , {'$set':{'users':users,'userdesc':userdesc}})
        if u and u['n']:
            return True
    except:
        logging.exception('mod_users_of_strategy failed. strategy_id:%s', strategy_id)
        raise ecode.DB_OP
    return False

def del_strategy( strategy_id):
    try:
        u = strategys.remove({'strategy_id':strategy_id})
        if u and u['n']:
            return True
    except:
        logging.exception('del_dev failed. dev_id:%s', dev_id)
    raise ecode.DB_OP


        

