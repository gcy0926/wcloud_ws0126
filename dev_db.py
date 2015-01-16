# -*- coding: utf8 -*-
#!/usr/bin/env python

import pymongo
import logging
import time
import ecode
import config


client = pymongo.MongoClient(config.get('mongo_host'), config.get('mongo_port'))
db = client[config.get('mongo_db')]
devs = db[config.get('mongo_dev_table')]


def init_db():
    devs.drop()
    devs.create_index([('dev_id',pymongo.ASCENDING)], unique=True)



def add_dev( dev_id, user ):
    if len(dev_id) <= 0:
        raise ecode.DATA_LEN_ERROR

    try:
        devs.create_index([('dev_id',pymongo.ASCENDING)], unique=True)

        t = str(int(time.time()))

        u = devs.update({'dev_id':dev_id}
                , {'$set':{'last_update':t,'cur_user':user}})
        if u and u['n']:
            return True

        if devs.insert({'dev_id':dev_id, 'loc':{'lon':'0','lat':'0'}
            ,'cmd_sn':0, 'cmds':[],'strategy_sn':0,'strategys':[],'current':{}, 'last_update':t,'cur_user':user}):
            return True
    except:
        logging.exception('add new dev failed. dev_id:%s', dev_id)
    raise ecode.DB_OP



def is_has_dev( dev_id ):
    try:
        r = devs.find_one({'dev_id':dev_id}, {'dev_id':1})
        if r:
            return True
    except:
        logging.exception('is_has_dev failed. dev_id:%s', dev_id)
        raise ecode.DB_OP
    return False

def del_dev( dev_id):
    try:
        u = devs.remove({'dev_id':dev_id})
        if u and u['n']:
            return True
    except:
        logging.exception('del_dev failed. dev_id:%s', dev_id)
    raise ecode.DB_OP


def new_cmd( dev_id, cmd):
    if len(cmd) <= 0:
        raise ecode.DATA_LEN_ERROR
    if len(cmd) > 256:
        raise ecode.DATA_LEN_ERROR

    try:
        r = devs.find_and_modify({'dev_id':dev_id},{'$inc':{'cmd_sn':1}}
                ,new=True,fields={'cmd_sn':1,'cmds':1})
        if len(r['cmds']) > 2:
            devs.update({'dev_id':dev_id}, {'$pop':{'cmds':-1}})

        u = devs.update({'dev_id':dev_id}, {'$push':{'cmds':
            {'id':r['cmd_sn'],'cmd':cmd}}})
        if u and u['n']:
            return True
    except:
        logging.exception('new_cmd failed. dev_id:%s', dev_id)
    raise ecode.DB_OP


def new_cmd_and_rs( dev_id, cmd,flog,res):
    if len(cmd) <= 0:
        raise ecode.DATA_LEN_ERROR
    if len(cmd) > 256:
        raise ecode.DATA_LEN_ERROR
    

    try:
        r = devs.find_and_modify({'dev_id':dev_id},{'$inc':{'cmd_sn':1}}
                ,new=True,fields={'cmd_sn':1,'cmds':1})
        if len(r['cmds']) > 2:
            devs.update({'dev_id':dev_id}, {'$pop':{'cmds':-1}})

        u = devs.update({'dev_id':dev_id}, {'$push':{'cmds':
            {'id':r['cmd_sn'],'cmd':cmd}}})
        s = devs.update({'dev_id':dev_id}, {'$set':{flog:res}})
        if u and u['n']and s and s['n']:
            return True
    except:
        logging.exception('new_cmd failed. dev_id:%s', dev_id)
    raise ecode.DB_OP

def get_cmds( dev_id):
    try:
        r = devs.find_one({'dev_id':dev_id}, {'cmds':1})
        return r['cmds']
    except:
        logging.exception('get_cmds failed. dev_id:%s', dev_id)
    raise ecode.DB_OP



def complete_cmd( dev_id, cmd_id ):
    try:
        u = devs.update({'dev_id':dev_id}
                , {'$pull':{'cmds':{'id':int(cmd_id)}}})
        if u and u['n']:
            return True
    except:
        logging.exception('complete_cmd failed. dev_id:%s', dev_id)
    raise ecode.DB_OP


def add_strategy(dev_id,strategy_id):  
    try:
        u = devs.update({'dev_id':dev_id}, {'$push':{'strategys':{'strategy_id':strategy_id,'is_read':"false"}}})           
        if u and u['n']:
            return True
    except:
        logging.exception('add_strategy failed. dev_id:%s', dev_id)
    raise ecode.DB_OP

def strategy_is_read(dev_id,strategy_id):
    try:
       stra = devs.find_one({'dev_id':dev_id},{'strategys':1})
       
       for s in stra['strategys']:
           if s['strategy_id']== strategy_id:
               s['is_read']="true"
               break
       u = devs.update({'dev_id':dev_id},{'$set':{"strategys":stra['strategys']}}) 
       if u and u['n']:
           return True             
    except:
        logging.exception('strategy_is_read failed. dev_id:%s', dev_id)
    raise ecode.DB_OP

def strategy_is_not_read(dev_id,strategy_id):
    try:
       stra = devs.find_one({'dev_id':dev_id},{'strategys':1})
       
       for s in stra['strategys']:
           if s['strategy_id']== strategy_id:
               s['is_read']="false"
               break
       u = devs.update({'dev_id':dev_id},{'$set':{"strategys":stra['strategys']}}) 
       if u and u['n']:
           return True             
    except:
        logging.exception('strategy_is_not_read failed. dev_id:%s', dev_id)
    raise ecode.DB_OP

def strategy_need_del(dev_id,strategy_id):
    try:
       stra = devs.find_one({'dev_id':dev_id},{'strategys':1})
       
       for s in stra['strategys']:
           if s['strategy_id']== strategy_id:
               s['is_read']="delete"
               break
       u = devs.update({'dev_id':dev_id},{'$set':{"strategys":stra['strategys']}}) 
       if u and u['n']:
           return True             
    except:
        logging.exception('strategy_need_delete failed. dev_id:%s', dev_id)
    raise ecode.DB_OP

def is_has_strategy_id(dev_id,strategy_id):
    try:
       stra = devs.find_one({'dev_id':dev_id},{'strategys':1})
       flog=0
       for s in stra['strategys']:
           if s['strategy_id']== strategy_id:
               flog=1
               break
       if flog == 1:
           return True
       else: 
           return False         
    except:
        logging.exception('is_has_strategy_id failed. dev_id:%s', dev_id)
    raise ecode.DB_OP

def get_strategy_ids(cur_user):
    try:
        r = devs.find_one({'cur_user':cur_user})
        if r.has_key('strategys'):
            return r['strategys']
        else:
            return []
    except:
        logging.exception('get_strategy_ids failed. cur_user:%s', cur_user)
    raise ecode.DB_OP
        
def complete_strategy( dev_id, strategy_id ):
    try:
        u = devs.update({'dev_id':dev_id}
                , {'$pull':{'strategys':{'strategy_id':strategy_id}}})
        if u and u['n']:
            return True
    except:
        logging.exception('complete_strategy failed. dev_id:%s', dev_id)
    raise ecode.DB_OP
'''
def new_strategy(dev_id,strategy):
    if dict != type(strategy):
        raise ecode.DATA_TYPE_ERROR
    if len(strategy) <= 0:
        raise ecode.DATA_LEN_ERROR
    if len(strategy) > 8:
        raise ecode.DATA_LEN_ERROR
    start=strategy['start']
    end=strategy['end']
    lon=strategy['lon']
    lat=strategy['lat']
    radius=strategy['radius']
    bluetooth=strategy['bluetooth']
    wifi=strategy['wifi']
    camera=strategy['camera']
    if str!=type(start)or str!=type(end):
        raise ecode.DATA_TYPE_ERROR
    if str!=type(lon)or str!=type(lat)or str !=type(radius):
        raise ecode.DATA_TYPE_ERROR
    if str!=type(bluetooth)or str!=type(wifi)or str!=type(camera):
        raise ecode.DATA_TYPE_ERROR
    if len(lon) <= 0 or len(lat) <= 0 or len(radius)<=0:
        raise ecode.DATA_LEN_ERROR
    try:
        r = devs.find_and_modify({'dev_id':dev_id},{'$inc':{'strategy_sn':1}}  
                ,new=True,fields={'strategy_sn':1,'strategys':1})
        if len(r['strategys']) > 0:
            devs.update({'dev_id':dev_id}, {'$pop':{'strategys':-1}})
        devs.update({'dev_id':dev_id}, {'$set':{'strategys':[]}})
        u = devs.update({'dev_id':dev_id}, {'$push':{'strategys':
        {'id':r['strategy_sn'],'start':start,'end':end
                                                ,'lon':lon,'lat':lat,'radius':radius
                                                ,'bluetooth': bluetooth
                                                ,'wifi':wifi
                                                ,'camera':camera}}})
        u = devs.update({'dev_id':dev_id}, {'$set':{'current':
                                                {'start':start,'end':end
                                                ,'lon':lon,'lat':lat,'radius':radius
                                                ,'bluetooth': bluetooth
                                                ,'wifi':wifi
                                                ,'camera':camera}}})
        if u and u['n']:
            return True
    except:
        logging.exception('new_strategy failed. dev_id:%s', dev_id)
        raise ecode.DB_OP

def get_strategys( dev_id):
    try:
        r = devs.find_one({'dev_id':dev_id}, {'strategys':1})
        return r['strategys']
    except:
        logging.exception('get_strategys failed. dev_id:%s', dev_id)
    raise ecode.DB_OP

def get_current_strategy( dev_id):
    try:
        r = devs.find_one({'dev_id':dev_id}, {'current':1})
        return r['current']
    except:
        logging.exception('get_current_strategy failed. dev_id:%s', dev_id)
    raise ecode.DB_OP
#闁圭瑳鍡╂斀濞戞搫鎷峰顖滅驳閺嶎偅娈�def complete_strategy( dev_id, strategy_id ):
    try:
        u = devs.update({'dev_id':dev_id}
                , {'$pull':{'strategys':{'id':int(strategy_id)}}})
        if u and u['n']:
            return True
    except:
        logging.exception('complete_strategy failed. dev_id:%s', dev_id)
    raise ecode.DB_OP
'''
def set_loc( dev_id, lon, lat):
    if len(lon) <= 0 or len(lat) <= 0:
        raise ecode.DATA_LEN_ERROR

    try:
        t = str(int(time.time()))

        u = devs.update({'dev_id':dev_id}
                , {'$set':{'loc':{'lon':lon,'lat':lat}
                    , 'last_update':t }})
        if u and u['n']:
            return True
    except:
        logging.exception('set_loc failed. dev_id:%s', dev_id)
    raise ecode.DB_OP


def get_loc( dev_id ):
    try:
        r = devs.find_one({'dev_id':dev_id}, {'loc':1})
        return r['loc']
    except:
        logging.exception('get_loc failed. dev_id:%s', dev_id)
    raise ecode.DB_OP

def set_rs( dev_id, info,rs):

    try:
        if (info == "wifi"):
            u = devs.update( {'dev_id':dev_id}, {'$set':{'wifi' :rs}})
        if (info == "bluetooth"):
            u = devs.update( {'dev_id':dev_id}, {'$set':{'bluetooth' :rs}})
 #       if (info == "camera"):
#            u = devs.update( {'dev_id':dev_id}, {'$set':{'camera' :rs}})
        if (info == "tape"):
            u = devs.update( {'dev_id':dev_id}, {'$set':{'tape' :rs}})
        if u and u['n']:
            return True
    except:
        logging.exception('set_rt failed. uid:%s', uid)
    raise ecode.DB_OP

def set_all_rs( dev_id,rs):

    try:
        u = devs.update( {'dev_id':dev_id}, {'$set':{'bluetooth':rs,'wifi':rs,'tape':rs}})
        if u and u['n']:
            return True
    except:
        logging.exception('set_all_rt failed. uid:%s', uid)
    raise ecode.DB_OP

def get_rs( dev_id, info):

    try:
        
        if (info == "wifi"):
            r = devs.find_one( {'dev_id':dev_id}, {'wifi' :1})
            return r['wifi']
        if (info == "bluetooth"):
            r = devs.find_one( {'dev_id':dev_id}, {'bluetooth' :1})
            return r['bluetooth']
 #       if (info == "camera"):
 #           r = devs.find_one( {'dev_id':dev_id}, {'camera' :1})
 #           return r['camera']
        if (info == "tape"):
            r = devs.find_one( {'dev_id':dev_id}, {'tape' :1})
            return r['tape']
    except:
        logging.exception('get_rt failed. dev_id:%s', dev_id)
    raise ecode.DB_OP

def get_last_update( dev_id ):
    try:
        r = devs.find_one({'dev_id':dev_id}, {'last_update':1})
        return r['last_update']
    except:
        logging.exception('get_last_update failed. dev_id:%s', dev_id)
    raise ecode.DB_OP


def get_static_info( dev_id, k ):
    try:
        r = devs.find_one({'dev_id':dev_id}, {'static_info':1})
        if r.has_key('static_info') and r['static_info'].has_key(k):
            return r['static_info'][k]
        else:
            return ''
    except:
        logging.exception('get_static_info failed. dev_id:%s', dev_id)
    raise ecode.DB_OP


def set_static_info( dev_id, k, v ):
    if len(k) <= 0 or len(v) <= 0:
        raise ecode.DATA_LEN_ERROR
    if len(k) > 32:
        raise ecode.DATA_LEN_ERROR
    if len(v) > 128:
        raise ecode.DATA_LEN_ERROR

    try:
        u = devs.update({'dev_id':dev_id}
                , {'$set':{'static_info.%s'%(k):v}})
        if u and u['n']:
            return True
    except:
        logging.exception('set_static_info failed. dev_id:%s', dev_id)
    raise ecode.DB_OP


def get_app_info( dev_id ):
    try:
        r = devs.find_one({'dev_id':dev_id}, {'app_info':1})
        if r.has_key('app_info'):
            return r['app_info']
        else:
            return ''
    except:
        logging.exception('get_app_info failed. dev_id:%s', dev_id)
    raise ecode.DB_OP


def set_app_info( dev_id, apps ):
    if len(apps) <= 0:
        raise ecode.DATA_LEN_ERROR

    try:
        u = devs.update({'dev_id':dev_id}
                , {'$set':{'app_info':apps}})
        if u and u['n']:
            return True
    except:
        logging.exception('set_app_info failed. dev_id:%s', dev_id)
    raise ecode.DB_OP




def get_web_app_info( dev_id ):
    try:
        r = devs.find_one({'dev_id':dev_id}, {'web_app_info':1})
        if r.has_key('web_app_info'):
            return r['web_app_info']
        else:
            return ''
    except:
        logging.exception('get_web_app_info failed. dev_id:%s', dev_id)
    raise ecode.DB_OP


def set_web_app_info( dev_id, apps ):
    if len(apps) <= 0:
        raise ecode.DATA_LEN_ERROR

    try:
        u = devs.update({'dev_id':dev_id}
                , {'$set':{'web_app_info':apps}})
        if u and u['n']:
            return True
    except:
        logging.exception('set_web_app_info failed. dev_id:%s', dev_id)
    raise ecode.DB_OP


def get_cur_user( dev_id ):
    try:
        r = devs.find_one({'dev_id':dev_id}, {'cur_user':1})
        if r :
            return r['cur_user']
        return ''
    except:
        logging.exception('get_cur_user failed. dev_id:%s', dev_id)
    raise ecode.DB_OP

def get_dev_id_by_curuser(curuser):
    try:
        r = devs.find_one({'cur_user':curuser},{'dev_id':1})
        if not r:
            return None
        return r['dev_id']
    except:
        logging.exception('get dev_id by cur_user failed. cur_user:%s',curuser)
    raise ecode.DB_OP

def add_IMSI( dev_id, IMSI ):
    if len(dev_id) <= 0:
        raise ecode.DATA_LEN_ERROR

    try:
        devs.create_index([('dev_id',pymongo.ASCENDING)], unique=True)

        u = devs.update({'dev_id':dev_id}
                , {'$addToSet':{'cur_IMSI':IMSI}})
        if u and u['n']:
            return True

    except:
        logging.exception('add new IMSI failed. dev_id:%s', dev_id)
    raise ecode.DB_OP

def get_dev_by_IMSI( IMSI ):
    try:
        r = devs.find_one({'cur_IMSI':IMSI}, {'dev_id':1})
        if r :
            return r['dev_id']
        return ''
    except:
        logging.exception('get_dev_by_IMSI failed. IMSI:%s', IMSI)
    raise ecode.DB_OP

def get_user_by_IMSI( IMSI ):
    try:
        r = devs.find_one({'cur_IMSI':IMSI}, {'cur_user':1})
        if r :
            return r['cur_user']
        return ''
    except:
        logging.exception('get_user_by_IMSI failed. IMSI:%s', IMSI)
    raise ecode.DB_OP

def change_dev(dev,IMSI,dev2):
    try:
        r=devs.update({'cur_IMSI':IMSI},{'$set':{'dev_id':''}})
        IMSI2=devs.find_one({'dev_id':dev2},{'cur_IMSI':1})
        r2=devs.update({'cur_IMSI':IMSI2},{'$set':{'dev_id':dev}})
        r3=devs.update({'cur_IMSI':IMSI},{'$set':{'dev_id':dev2}})
        if r:
            return True
        elif r2:
            return True
        elif r3:
            return True
        return False
    except:
        logging.exception('change_dev dev_db failed. IMSI:%s', IMSI)
    raise ecode.DB_OP
