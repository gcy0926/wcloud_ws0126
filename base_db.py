# -*- coding: utf8 -*-
#!/usr/bin/env python

import pymongo
import logging
import time
import ecode
import config


client = pymongo.MongoClient(config.get('mongo_host'), config.get('mongo_port'))
db = client[config.get('mongo_db')]
base = db[config.get('mongo_base_table')]


def init_db():
    base.drop()


def add_base( lon,lat, baseStationId,radius=2000 ):
    if len(lon) <= 0:
        raise ecode.DATA_LEN_ERROR
    if len(lat) <= 0:
        raise ecode.DATA_LEN_ERROR

    try:
        t = str(int(time.time()))

        if base.find_one({'lon':lon,'lat':lat},{'lon':1}):
            u=base.update({'lon':lon,'lat':lat},{'$set':{'baseStationId':baseStationId,'radius':radius}})
            if u and u['n']:
                return True
        else:
            if base.insert({'lon':lon,'lat':lat,'baseStationId':baseStationId, 'radius':radius}):
                return True
    except:
        logging.exception('add new basestationid failed. lon:%s，lat:%s', lon,lat)
    raise ecode.DB_OP

def get_basestationid(lon,lat):
    try:
        r = base.find_one({'lon':lon,'lat':lat}, {'baseStationId':1})
        if r:
            return r['baseStationId']
        else:
            return ''
    except:
        logging.exception('get_basestationid failed. loc:%s', loc)
    raise ecode.DB_OP



