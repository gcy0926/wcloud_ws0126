# -*- coding: utf8 -*-
#!/usr/bin/env python

import hashlib
import sha
import random
import redis
import logging
import config


rdb = None
def get_db():
    global rdb
    if not rdb:
        rdb =  redis.Redis( host=config.get('redis_host')
                , port=config.get('redis_port')
                , db=config.get('redis_captcha_db'))
    return rdb


def add( cid, value ):
    if len(cid) <= 0 or len(value) <= 0:
        return False

    try:
        get_db().set( cid, value)
    except Exception,ex:
        logging.exception('add captcha failed. cid:%s,value:%s'
                , cid, value)
        return False
    return True


def get( cid ):
    value = ''
    try:
        value = get_db().get(cid)
        if not value:
            value = ''
    except Exception,ex:
        logging.exception('get captcha failed. cid:%s', cid)
    return value


def getandrm( cid ):
    value = ''
    try:
        value = get_db().get( cid)
        if not value:
            value = ''
        else:
            get_db().delete( cid )
    except Exception,ex:
        logging.exception('get captcha failed. cid:%s', cid)
    return value


def rm( cid ):
    try:
        get_db().delete( cid )
    except Exception,ex:
        logging.exception('rm captcha failed. cid:%s', cid)


