# -*- coding: utf8 -*-
#!/usr/bin/env python

import sys
import os
import json
import urllib
import httplib
import time
import ecode
import re
import config


# sms template
sms_init_pw = 0
sms_new_pw = 1


class SMS_189:
    app_id = '373745620000031915'
    app_secret = '8f8243366ee5f6b72e21f29ff8cf92f0'
    access_token = ''

    def _get_at(self):
        h = httplib.HTTPSConnection( 'oauth.api.189.cn' )
        params = urllib.urlencode( {'grant_type':'client_credentials'
            , 'app_id': self.app_id
            , 'app_secret': self.app_secret } )
        h.request('POST', '/emp/oauth2/v2/access_token', body=params
                , headers={'Content-Type': 'application/x-www-form-urlencoded'})
        rt = json.loads(h.getresponse().read())
        if rt['res_code'] == '0':
            self.access_token = rt['access_token']
    
        return int(rt['res_code'])

    
    def _send_sms(self, pnumber, temp_id, temp_param):
        h = httplib.HTTPConnection( 'api.189.cn' )
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        params = urllib.urlencode( sorted({'app_id': self.app_id
            , 'access_token':self.access_token
            , 'acceptor_tel':pnumber
            , 'template_id' : temp_id
            , 'template_param': temp_param
            , 'timestamp': timestamp }.items()))
    
        h.request('POST', '/v2/emp/templateSms/sendSms', body=params
                , headers={'Content-Type': 'application/x-www-form-urlencoded'})
        rt = json.loads(h.getresponse().read())
        return int(rt['res_code'])


    def send_sms(self, pnumber, temp, temp_param ):
        temp_id = ''
        if temp == sms_init_pw:
            temp_id = '91000062'
        elif temp == sms_new_pw:
            temp_id = '91000065'
        else:
            return 1

        temp_param_json = json.dumps({'pnumber':pnumber,'pw':pw})

        rt = self._send_sms( pnumber, temp_id, temp_param_json)
        if rt != 0:
            self._get_at()
            rt = self._send_sms( pnumber, temp_id, temp_param_json)
        if rt == 0:
            return True


class SMS_bechtech:
    def send_sms(self, pnumber, temp, temp_param ) : 
        content = ''
        if temp == sms_init_pw:
            content = '尊敬的%s用户，您的WorkPhone新密码为：%s，感谢您的使用！【WorkPhone】'%(
                    str(temp_param['pnumber']), str(temp_param['pw']))
        elif temp == sms_new_pw:
            content = '尊敬的%s用户，您的WorkPhone初始密码为：%s，感谢您的使用！【WorkPhone】'%(
                    str(temp_param['pnumber']), str(temp_param['pw']))
        else:
            raise ecode.SMS_TEMP_ERROR
    
        result = 0
        try:
            h = httplib.HTTPConnection( 'sms.bechtech.cn' )
            params = urllib.urlencode( {'accesskey': '1489' 
                , 'secretkey':'a5ac118de83b928ba166ce7d446b10915eb1ff03'
                , 'mobile': str(pnumber)
                , 'content' : content})
    
            h.request('GET', '/Api/send/data/json?%s'%(params) )
            rt = json.loads(h.getresponse().read())
            result = int(rt['result'])
        except Exception as e:
            logging.exception('SMS_bechtech send sms.')
            raise ecode.SMS_REQ_API_ERROR

        if result != 1:
            raise ecode.SMS_API_RES_ERROR

    


sms_sender = SMS_bechtech()


def send_inital_pw( pnumber, pw):
    if config.check_debug_acc(pnumber):
        return

    temp_param = {'pnumber':pnumber,'pw':pw}
    sms_sender.send_sms( pnumber, sms_init_pw, temp_param )


def send_new_passwd( pnumber, pw):
    if config.check_debug_acc(pnumber):
        return

    temp_param = {'pnumber':pnumber,'pw':pw}
    sms_sender.send_sms( pnumber, sms_new_pw, temp_param )


pn_compile = re.compile(r'1\d{10}')
def check_pnumber(pnumber):
    if len(pnumber) != 11:
        return False
    if not pn_compile.match(pnumber):
        return False
    return True

