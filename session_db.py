# -*- coding: utf8 -*-
#!/usr/bin/env python

import hashlib
import sha
import random
import redis
import logging
import config



class Session:
    rdb = None
    def connect_db(self):
        if not self.rdb:
            self.rdb =  redis.Redis(
                    host=config.get('redis_host')
                    ,port=config.get('redis_port')
                    , db=config.get('redis_session_db'))


    def create(self, uid, dev_id, ip ):
        ip = 'no_use'
        if len(uid) <= 0 or len(dev_id) <= 0 or len(ip) <= 0:
            return ''

        self.connect_db()
        sid = ''
        try:
            oldsid = self.rdb.hget(uid, dev_id)
            if oldsid:
                self.del_by_user(uid,dev_id)

            # make sid
            s = sha.new()
            s.update(str(random.random()))
            s.update(uid)
            s.update(ip)
            s.update(dev_id)
            sid = s.hexdigest()

            # add session info to  rdb
            val = "%s:%s"%(sid,ip)
            self.rdb.hset(uid, dev_id, val)
            self.rdb.set(val, "%s:%s"%(uid,dev_id))
        except Exception,ex:
            sid = ''
            logging.exception('create sid failed. uid:%s,dev_id:%s,ip:%s'
                    , uid, dev_id, ip)

        return sid


    def del_by_user(self, uid, dev_id):
        self.connect_db()
        try:
            s = self.rdb.hget(uid, dev_id)
            if s:
                self.rdb.delete(s)
                self.rdb.hdel(uid,dev_id)
        except Exception,ex:
            logging.exception('del_by_user failed. uid:%s,dev_id:%s'
                    , uid, dev_id)


    def del_by_sid(self, sid, ip):
        ip = 'no_use'
        self.connect_db()
        try:
            s = "%s:%s"%(sid,ip)
            uid,dev_id = self.rdb.get(s).split(':')
            if uid and dev_id:
                self.rdb.delete(s)
                self.rdb.hdel(uid,dev_id)
        except Exception,ex:
            logging.exception('del_by_sid failed. sid:%s,ip:%s'
                    , sid, ip)


    def get_sid(self, uid, dev_id ):
        self.connect_db()
        sid=''
        try:
            
            if self.rdb.hget(uid, dev_id):
                sid,ip = self.rdb.hget(uid, dev_id).split(':')

        except Exception,ex:
            sid = ''
            logging.exception('get_sid failed. uid:%s,dev_id:%s'
                    , uid, dev_id)
        return sid


    def get_user(self, sid, ip ):
        ip = 'no_use'
        self.connect_db()
        try:
            u,d = self.rdb.get("%s:%s"%(sid,ip)).split(':')
        except Exception,ex:
            u = ''
            logging.exception('get_user failed. sid:%s,ip:%s'
                    , sid, ip)
        return u


    def get_user_and_dev(self, sid, ip ):
        ip = 'no_use'
        self.connect_db()
        try:
            u,d = self.rdb.get("%s:%s"%(sid,ip)).split(':')
        except Exception,ex:
            u = ''
            d = ''
            logging.exception('get_user failed. sid:%s,ip:%s'
                    , sid, ip)
        return u,d


user = Session()

