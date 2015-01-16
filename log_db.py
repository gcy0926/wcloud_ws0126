# -*- coding: utf8 -*-
#!/usr/bin/env python

import pymongo
import logging
import time
import ecode
import config


client = pymongo.MongoClient(config.get('mongo_host'), config.get('mongo_port'))
db = client[config.get('mongo_db')]
table = db[config.get('mongo_log_table')]


def init_db():
    devs.drop()


def add_log( uid, dev_id, t, app, action, info):
    if len(dev_id) <= 0 or len(uid) <= 0 or len(t) <= 0 or len(action) <= 0:
        raise ecode.DATA_LEN_ERROR

    try:
        if table.insert({'uid':uid, 'dev_id':dev_id, 't':t, 'app':app
            ,'act':action, 'info':info}):
            return True
    except:
        logging.exception('add log:%s %s', uid, dev_id)
    raise ecode.DB_OP



def get_logs( uid, dev_id ):
    if len(uid) <= 0 or len(dev_id) <= 0:
        raise ecode.DATA_LEN_ERROR
    logs = []
    try:
        r = table.find( {'uid':uid,'dev_id':dev_id}
                , {'_id':0,'t':1,'app':1,'act':1,'info':1})

        for item in r.sort([('t',1)]).limit(100):
            logs.append(item)
        return logs
    except:
        logging.exception('get log failed. %s %s', uid,dev_id)
    raise ecode.DB_OP


