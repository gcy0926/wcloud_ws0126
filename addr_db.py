# -*- coding: utf8 -*-
#!/usr/bin/env python


import pymongo
import logging
import time
import ecode
import config
import re
import baseStation


client = pymongo.MongoClient(config.get('mongo_host'), config.get('mongo_port'))
db = client[config.get('mongo_db')]
table = db[config.get('mongo_addr_table')]



def init_db():
    table.drop()
    table.create_index([('org_name',pymongo.ASCENDING)], unique=True)


def is_has_org( org_name ):
    try:
        r = table.find_one({'org_name': org_name}, {'org_name':1})
        if r:
            return True
    except:
        logging.exception('is_has_org failed. org_name:%s', org_name)
        raise ecode.DB_OP
    return False


def add_org( org_name, push_serv, ws_serv, wf_serv, eg_serv ):
    if len(org_name) <= 0:
        raise ecode.DATA_LEN_ERROR

    if is_has_org( org_name ):
        raise ecode.EXIST_ORG

    try:
        if table.insert({'org_name':org_name
            , 'push_serv':push_serv
            , 'ws_serv':ws_serv
            , 'wf_serv':wf_serv
            , 'eg_serv':eg_serv}):
            return True
    except:
        logging.exception('add new org failed. org_name:%s', org_name)
    raise ecode.DB_OP



def del_org( org_name):
    try:
        u = table.remove({'org_name':org_name})
        if u and u['n']:
            return True
    except:
        logging.exception('del_org failed. org_name:%s', org_name)
    raise ecode.DB_OP


def get( org_name ):
    r = None
    try:
        #调用get获取orgaddr之前，先从ini中导入数据库中
#        addr={}   #存从ini配置文件中读到的地址信息
#        addr_items=baseStation.get_org_addr('addr')
#        for item in addr_items:
#            addr[item[0]]=item[1]
#        logging.error('addr from ini is : %s',addr)
            
        #将读入的地址信息存入数据库
#        if not table.find({'org_name':org_name}):
#            raise
#        else:
#            table.update({'org_name':org_name}, {'$set':addr})
        
        r = table.find_one({'org_name':org_name},{'_id':0})
    except:
        logging.exception('get failed. org_name:%s', org_name)
        raise ecode.DB_OP
    if not r:
        raise ecode.NOT_EXIST_ORG
    return r


def get_org_list():
    try:
        table.drop()
        table.create_index([('org_name',pymongo.ASCENDING)], unique=True)
        #调用get获取orgaddr之前，先从ini中导入数据库中
        addr={}   #存从ini配置文件中读到的地址信息
        addr_items=baseStation.get_org_addr('addr')
        for item in addr_items:
            addr[item[0]]=item[1]
            logging.error('addr from ini is : %s',addr)
        table.insert(addr)
            
        ol = []
        for item in table.find({}, {'_id':0,'org_name':1}):
            ol.append( item['org_name'] )
                
        return ol

    except:
        logging.exception('get failed. org_name:%s', ol)
    raise ecode.DB_OP





