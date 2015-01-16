# -*- coding: utf8 -*-

import web
import logging
import sha
import os

import ws_io
import ecode
import session_db
import org
import user_ldap
import user_db
import dev_db
import log_db
import cert_db
import config
import admin_db
import trace
import time
import baseStation




class Login:
    #{{{
    def POST(self):
        """
        input:
            uid: user id
            pw: password
        output:
            rt: error code
            sid: session id
            is_config_ok: is this org acc config finish?
        """
        rt = ecode.FAILED
        sid = ''
        is_config_ok = 1 

        try:
            i = ws_io.ws_input(['uid','pw'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            org_config = org.get_config()
            #如果用户不是最高级管理员
            if org_config['admin'] != i['uid']:
                #监测是否为单位管理员
                if not admin_db.is_has_admin(i['uid']):
                    raise ecode.USER_NOT_EXIST
                else:
                    if not admin_db.check_pw(i['uid'],sha.new(i['pw']).hexdigest()):
                        raise ecode.USER_AUTH                                                          
            else: 
                if org_config['admin_pw'] != sha.new(i['pw']).hexdigest():
                    raise ecode.USER_AUTH

            # create session
            sid = session_db.user.create( i['uid'], 'admin', web.ctx.ip)
            if not sid:
                raise ecode.SDB_OP

            if not org_config['ldap_host']:
                is_config_ok = 0

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('org admin login')

        return ws_io.ws_output(dict(rt=rt.eid,sid=sid,is_config_ok=is_config_ok))
    #}}}


class Logout:
    #{{{
    def POST(self):
        """
        input:
            sid: 

        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT

            session_db.user.del_by_sid( i['sid'], web.ctx.ip)

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('Logout')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}


class SetPW:
    #{{{
    def POST(self):
        """
        input:
            sid: 
            oldpw:
            newpw:

        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['sid','oldpw','newpw'])
            if not i:
                raise ecode.WS_INPUT

            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP

            if not config.check_pw_rule( i['newpw']) :
                raise ecode.PW_RULE

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION
                else:
                    if admin_db.get_pw_by_uid(user)!= sha.new(i['oldpw']).hexdigest():
                        raise ecode.OLD_PW_ERROR
                    else:
                        if not admin_db.update_pw(user,sha.new(i['newpw']).hexdigest()):
                            raise ecode.DB_OP                   
            else:
                if org_config['admin_pw'] != sha.new(i['oldpw']).hexdigest():
                    raise ecode.OLD_PW_ERROR
                if not org.update_config({'admin_pw':sha.new(i['newpw']).hexdigest()}):
                    raise ecode.DB_OP

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('setpw')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}


class OrgInfo:
    #{{{
    def POST(self):
        """
        input:
            sid: session id
            auth_mode:0
            org_name:''
            org_addr:''
            admin_pnumber:''
            admin_email:''
        output:
            rt: error code
        """
        rt = ecode.FAILED
        sid = ''

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                raise ecode.NOT_PERMISSION

            kv_table = {}
            if i.has_key('auth_mode'):
                kv_table['auth_mode'] = int(i['auth_mode'])
            if i.has_key('org_name'):
                kv_table['org_name'] = i['org_name']
            if i.has_key('org_addr'):
                kv_table['org_addr'] = i['org_addr']
            if i.has_key('admin_pnumber'):
                kv_table['admin_pnumber'] = i['admin_pnumber']
            if i.has_key('admin_email'):
                kv_table['admin_email'] = i['admin_email']

            if not org.update_config(kv_table):
                raise ecode.DB_OP

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('set org info')

        return ws_io.ws_output(dict(rt=rt.eid))


    def GET(self):
        """
        input:
            sid: session id
        output:
            rt: error code
            auth_mode:0
            org_name:''
            org_right:''
            admin_email:''
        """
        rt = ecode.FAILED
        auth_mode=0
        admin_name=''
        org_right=''
        #org_addr=''
        #admin_pnumber=''
        admin_email=''

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION
                else:
                    org_right,admin_email = admin_db.get_ou_and_email_by_uid(user)
                    auth_mode = org_config['auth_mode']
                    admin_name = user
                    
            else:
                auth_mode = org_config['auth_mode']
                admin_name = org_config['org_name']
                org_right = "所有用户"
                admin_email = org_config['admin_email']

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get org info')

        return ws_io.ws_output(dict(rt=rt.eid,auth_mode=auth_mode
            ,org_right=org_right,admin_name=admin_name,admin_email=admin_email))
    #}}}


class LdapConfig:
    #{{{
    def POST(self):
        """
        input:
            sid: session id
            ldap_host: ''
            ldap_port:389
            ldap_base_dn:''
            ldap_user_dn:''
            ldap_pw:''
            ldap_at_uid:''
            ldap_at_allow_use:''
            ldap_at_pnumber:''
            ldap_at_email:''
        output:
            rt: error code
        """
        rt = ecode.FAILED
        sid = ''

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                
                raise ecode.NOT_PERMISSION

            kv_table = {}
            if i.has_key('ldap_host'):
                kv_table['ldap_host'] = i['ldap_host']
            if i.has_key('ldap_port'):
                kv_table['ldap_port'] = int(i['ldap_port'])
            if i.has_key('ldap_base_dn'):
                kv_table['ldap_base_dn'] = i['ldap_base_dn']
            if i.has_key('ldap_user_dn'):
                kv_table['ldap_user_dn'] = i['ldap_user_dn']
            if i.has_key('ldap_pw'):
                kv_table['ldap_pw'] = i['ldap_pw']
            if i.has_key('ldap_at_uid'):
                kv_table['ldap_at_uid'] = i['ldap_at_uid']
            if i.has_key('ldap_at_allow_use'):
                kv_table['ldap_at_allow_use'] = i['ldap_at_allow_use']
            if i.has_key('ldap_at_pnumber'):
                kv_table['ldap_at_pnumber'] = i['ldap_at_pnumber']
            if i.has_key('ldap_at_email'):
                kv_table['ldap_at_email'] = i['ldap_at_email']

            if not org.update_config(kv_table):
                raise ecode.DB_OP

            org_config = org.get_config()
            uldap = user_ldap.create_ldap( ip = org_config['ldap_host']
                    , port = org_config['ldap_port']
                    , base_dn = org_config['ldap_base_dn']
                    , user_dn = org_config['ldap_user_dn']
                    , pw = org_config['ldap_pw']
                    , at_uid = org_config['ldap_at_uid']
                    , at_allow_use = org_config['ldap_at_allow_use']
                    , at_pnumber = org_config['ldap_at_pnumber']
                    , at_email = org_config['ldap_at_email'])

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('set org ldap config')

        return ws_io.ws_output(dict(rt=rt.eid))


    def GET(self):
        """
        input:
            sid: session id
        output:
            rt: error code
            ldap_host: ''
            ldap_port:389
            ldap_base_dn:''
            ldap_user_dn:''
            ldap_pw:''
            ldap_at_uid:''
            ldap_at_allow_use:''
            ldap_at_pnumber:''
            ldap_at_email:''
        """
        rt = ecode.FAILED
        ldap_host =  ''
        ldap_port = 389
        ldap_base_dn = ''
        ldap_user_dn = ''
        ldap_pw = ''
        ldap_at_uid = ''
        ldap_at_allow_use = ''
        ldap_at_pnumber = ''
        ldap_at_email = ''

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
#             if user != org_config['admin']:
#                 raise ecode.NOT_PERMISSION
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION
                
            ldap_host = org_config['ldap_host']
            ldap_port = org_config['ldap_port']
            ldap_base_dn = org_config['ldap_base_dn']
            ldap_user_dn = org_config['ldap_user_dn']
            ldap_pw = org_config['ldap_pw']
            ldap_at_uid = org_config['ldap_at_uid']
            ldap_at_allow_use = org_config['ldap_at_allow_use']
            ldap_at_pnumber = org_config['ldap_at_pnumber']
            ldap_at_email = org_config['ldap_at_email']

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get org ldap config info')

        return ws_io.ws_output(dict(rt=rt.eid
            ,ldap_host = ldap_host
            ,ldap_port = ldap_port
            ,ldap_base_dn = ldap_base_dn
            ,ldap_user_dn = ldap_user_dn
            ,ldap_pw = ldap_pw
            ,ldap_at_uid = ldap_at_uid
            ,ldap_at_allow_use = ldap_at_allow_use
            ,ldap_at_pnumber = ldap_at_pnumber
            ,ldap_at_email = ldap_at_email))
    #}}}



class LdapUsers:
    #{{{
    def GET(self):
        """
        input:
            sid: sesssion id
        output:
            rt: error code
            users:[{uid:'',email:'',pnumber:'',username:'','dn':'','ou':''},{}]
            nau_users:[{uid:'',email:'',pnumber:'',username:'','dn':'','ou':''},{}]
        """
        rt = ecode.FAILED
        users = []
        nau_users = []

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
#             if user != org_config['admin']:
#                 raise ecode.NOT_PERMISSION
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION
            

            uldap = user_ldap.create_ldap( ip = org_config['ldap_host']
                    , port = org_config['ldap_port']
                    , base_dn = org_config['ldap_base_dn']
                    , user_dn = org_config['ldap_user_dn']
                    , pw = org_config['ldap_pw']
                    , at_uid = org_config['ldap_at_uid']
                    , at_allow_use = org_config['ldap_at_allow_use']
                    , at_pnumber = org_config['ldap_at_pnumber']
                    , at_email = org_config['ldap_at_email']
                    , at_username = org_config['ldap_at_username']
                    , at_dn = org_config['ldap_at_dn']
                    , at_ou = org_config['ldap_at_ou']
                    , at_job = org_config['ldap_at_job'])
            
            for u in uldap.get_all_users():
                uinfo =  u[1]
                if not uinfo.has_key(org_config['ldap_at_uid']):
                    continue
                uid = uinfo[org_config['ldap_at_uid']]
                if type(uid) is list:
                    uid = uid[0]

                if not uinfo.has_key(org_config['ldap_at_allow_use']):
                    continue
                allow_use = uinfo[org_config['ldap_at_allow_use']]
                if type(allow_use) is list:
                    allow_use = allow_use[0]

                email = ''
                if uinfo.has_key(org_config['ldap_at_email']):
                    email = uinfo[org_config['ldap_at_email']]
                    if type(email) is list:
                        email = email[0]

                pnumber = ''
                if uinfo.has_key(org_config['ldap_at_pnumber']):
                    pnumber = uinfo[org_config['ldap_at_pnumber']]
                    if type(pnumber) is list:
                        pnumber = pnumber[0]
                username = ''
                if uinfo.has_key(org_config['ldap_at_username']):
                    username = uinfo[org_config['ldap_at_username']]
                    if type(username) is list:
                        username = username[0]
                dn = str(u[0])
                #if uinfo.has_key(org_config['ldap_at_dn']):
                    #dn = uinfo[org_config['ldap_at_dn']]
                    #if type(dn) is list:
                        #dn = dn[0]

                if allow_use == 'Y':
                    users.append( {'uid':uid,'email':email, 'pnumber':pnumber, 'username':username, 'dn':dn} )
                else:
                    nau_users.append( {'uid':uid,'email':email, 'pnumber':pnumber, 'username':username, 'dn':dn} )

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get ldap users')

        return ws_io.ws_output(dict(rt=rt.eid, users=users,nau_users=nau_users))
    #}}}
    
    
class LdapOus:
    #{{{
    def GET(self):
        """
        input:
            sid: sesssion id
        output:
            rt: error code
            ous:['dn':'','ou':''},{}]
        """
        rt = ecode.FAILED
        ous = []

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                raise ecode.NOT_PERMISSION

            uldap = user_ldap.create_ldap( ip = org_config['ldap_host']
                    , port = org_config['ldap_port']
                    , base_dn = org_config['ldap_base_dn']
                    , user_dn = org_config['ldap_user_dn']
                    , pw = org_config['ldap_pw']
                    , at_uid = org_config['ldap_at_uid']
                    , at_allow_use = org_config['ldap_at_allow_use']
                    , at_pnumber = org_config['ldap_at_pnumber']
                    , at_email = org_config['ldap_at_email']
                    , at_username = org_config['ldap_at_username']
                    , at_dn = org_config['ldap_at_dn']
                    , at_ou = org_config['ldap_at_ou']
                    , at_job = org_config['ldap_at_job'])
            
            for ou in uldap.get_all_ous():
                ouinfo =  ou[1]
                dn = str(ou[0])
                ous.append( {'ou':ouinfo['ou'], 'dn':dn} )
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get ldap users')

        return ws_io.ws_output(dict(rt=rt.eid, ous=ous))
    #}}}

class LdapOneLevel:
    #{{{
    def GET(self):
        """
        input:
            sid: sesssion id
            oudn: oudn在前台点击群组时获得的群组dn
        output:
            rt: error code
            ous:[{'dn':'','ou':''},{}]
            users:[{'dn':'',uid:'',email:'',pnumber:'',username:''},{}]授权的用户
        """
        rt = ecode.FAILED
        ous = []
        users = []
        
        org_config = org.get_config()
        ip = org_config['ldap_host']
        port = org_config['ldap_port']
        base_dn = org_config['ldap_base_dn']
        user_dn = org_config['ldap_user_dn']
        pw = org_config['ldap_pw']
        at_uid = org_config['ldap_at_uid']
        at_allow_use = org_config['ldap_at_allow_use']
        at_pnumber = org_config['ldap_at_pnumber']
        at_email = org_config['ldap_at_email']
        at_username = org_config['ldap_at_username']
        at_dn = org_config['ldap_at_dn']
        at_ou = org_config['ldap_at_ou']
        at_job = org_config['ldap_at_job']

        try:
            i = ws_io.ws_input(['sid','oudn'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION

            uldap = user_ldap.create_ldap( ip, port , base_dn , user_dn , pw , at_uid , at_allow_use 
                    , at_pnumber 
                    , at_email 
                    , at_username 
                    , at_dn 
                    , at_ou
                    , at_job )
            
            for onelevel in uldap.get_all_onelevel(i['oudn']):
                info =  onelevel[1]
                dn = str(onelevel[0])
                if not info.has_key(at_uid):
                    if not info.has_key(at_ou):
                        continue
                    ou = info[at_ou]
                    if type(ou) is list:
                        ou = ou[0]
                    ous.append({'dn':dn,'ou':ou})
                else:
                    if not info.has_key(at_allow_use):
                        continue
                    allow_use = info[at_allow_use]
                    if type(allow_use) is list:
                        allow_use = allow_use[0]
                    #这个逻辑很重要，因为返回来的很有可能就是一个列表结构，只是表明上输出是字符
                    uid = info[at_uid]
                    if type(uid) is list:
                        uid = uid[0]
    
                    username = ''
                    if info.has_key(at_username):
                        username = info[at_username]
                        if type(username) is list:
                            username = username[0];
                                
                    pnumber = ''
                    if info.has_key(pnumber):
                        pnumber = info[at_pnumber]
                        if type(pnumber) is list:
                            pnumber = pnumber[0];
                            
                    if allow_use=='Y':
                        users.append( {'dn':dn, 'uid':uid,'username':username,'pnumber':pnumber} )
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get ldap onelevel')

        return ws_io.ws_output(dict(rt=rt.eid, ous=ous, users=users))
    #}}}
    
class StaticUserInfo:
    #{{{
    def GET(self):
        """
        input:
            sid: sesssion id
            oudn: oudn在前台点击群组时获得的群组dn
        output:
            rt: error code
            ous:[{'dn':'','ou':''},{}]
            users:[{'dn':'',uid:'',email:'',pnumber:'',username:''},{}]授权的用户
        """
        rt = ecode.FAILED
        all = {}
        
        try:
            s = ''.join([line.rstrip() for line in open('ocr.txt')]) 
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get ldap onelevel')

        return ws_io.ws_output(dict(rt=rt.eid, ous=ous, users=users))
    #}}}


class LdapTree:
    #{{{
    '''
    org_config = org.get_config()
    ip = org_config['ldap_host']
    port = org_config['ldap_port']
    base_dn = org_config['ldap_base_dn']
    user_dn = org_config['ldap_user_dn']
    pw = org_config['ldap_pw']
    at_uid = org_config['ldap_at_uid']
    at_allow_use = org_config['ldap_at_allow_use']
    at_pnumber = org_config['ldap_at_pnumber']
    at_email = org_config['ldap_at_email']
    at_username = org_config['ldap_at_username']
    at_dn = org_config['ldap_at_dn']
    at_ou = org_config['ldap_at_ou']
    '''
    org_config = org.get_config()
    global ip 
    ip = org_config['ldap_host']
    global port 
    port= org_config['ldap_port']
    global base_dn
    base_dn = org_config['ldap_base_dn']
    
    global user_dn 
    user_dn = org_config['ldap_user_dn']
    global pw 
    pw = org_config['ldap_pw']
    global at_uid
    at_uid = org_config['ldap_at_uid']
    global at_allow_use 
    at_allow_use = org_config['ldap_at_allow_use']
    global at_pnumber 
    at_pnumber = org_config['ldap_at_pnumber']
    global at_email
    at_email = org_config['ldap_at_email']
    global at_username 
    at_username = org_config['ldap_at_username']
    global at_dn 
    at_dn = org_config['ldap_at_dn']
    global at_ou 
    at_ou = org_config['ldap_at_ou']
    global at_job
    at_job = org_config['ldap_at_job']

    global uldap
    uldap = user_ldap.create_ldap( ip, port , base_dn , user_dn , pw , at_uid , at_allow_use 
                    , at_pnumber 
                    , at_email 
                    , at_username 
                    , at_dn 
                    , at_ou
                    , at_job )
    def GET(self):
        """
        input:
            sid: sesssion id
        output:
            rt: error code
            ous:[{'dn':'','ou':''},{}]
            users:[{'dn':'',uid:'',email:'',pnumber:'',username:''},{}]授权的用户
        """
        rt = ecode.FAILED
        all = {}
        try:
            org_config = org.get_config()
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN
            """
                                    如果登陆用户不是高级管理员,判定是否为单位管理员，如果是，则只加载该单位的人员信息
            """
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION
                else:
                    ou = admin_db.get_ou_by_uid(user)
                    oudn = "ou="+ou+","+org_config['ldap_base_dn']
                    all = LdapTree().get_all_sons(oudn,ou)
            else:
                all = LdapTree().get_all_sons(org_config['ldap_base_dn'],org_config['admin'])
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get ldap tree')

        return ws_io.ws_output(dict(rt=rt.eid, all=all))
 

    def get_all_sons(self,oudn,ouname):
        """get all users and ous on one level for the oudn"""
        #查找同一层级SCOPE_ONELEVEL
        #基于群组的dn查找,找到自己所有的子节点 
        #读取配置文件中的内容
        
        sons = uldap.get_all_onelevel(oudn)#找到基准节点的所有下一层级子节点
        ous=[]
        users=[]
        for son in sons:   
            info = son[1]
            dn = str(son[0])
            if not dn:
                continue
            else:
                if not info.has_key(at_uid):
                    if info.has_key(at_ou):
                        ou = info.get(at_ou)
                        if type(ou) is list:
                            ou = ou[0]
                        sons2 = LdapTree().get_all_sons(dn,ou);
                        if not sons2:
                            continue
                        else:
                            ous.append(sons2)
                else:
                    if not info.has_key(at_allow_use):
                        continue
                    allow_use = info[at_allow_use]
                    if type(allow_use) is list:
                        allow_use = allow_use[0]
                        #这个逻辑很重要，因为返回来的很有可能就是一个列表结构，只是表明上输出是字符
                    uid = info[at_uid]
                    if type(uid) is list:
                        uid = uid[0]
    
                    username = ''
                    if info.has_key(at_username):
                        username = info[at_username]
                        if type(username) is list:
                            username = username[0];
                                
                    pnumber = ''
                    if info.has_key(at_pnumber):
                        pnumber = info[at_pnumber]
                        if type(pnumber) is list:
                            pnumber = pnumber[0];
                    #+++ 11.13        
                    email = ''
                    if info.has_key(at_email):
                        email = info[at_email]
                        if type(email) is list:
                            email = email[0];
                            
                    job = ''
                    if info.has_key(at_job):
                        job = info[at_job]
                        if type(job) is list:
                            job = job[0];
                            
                    if allow_use=='Y':
                        users.append( {'dn':dn, 'uid':uid,'username':username,'pnumber':pnumber,'job':job,'email':email})
                    
        return {'dn':oudn,'ou':ouname,'ous':ous,'users':users}
            
    #}}}

class LdapAll:
    #{{{
    def GET(self):
        '''
        input:
            sid:session id
                        这个其实也得考虑一下以后的扩展，将根节点信息写在配置文件中应该是没问题
        output:
            rt:error code
            all:{'dn':dn,'ou':ou,'ous':[],'users':[]}
        '''
        rt = ecode.FAILED
        all = {}
        ous = []
        users = []

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                raise ecode.NOT_PERMISSION

            uldap = user_ldap.create_ldap( ip = org_config['ldap_host']
                    , port = org_config['ldap_port']
                    , base_dn = org_config['ldap_base_dn']
                    , user_dn = org_config['ldap_user_dn']
                    , pw = org_config['ldap_pw']
                    , at_uid = org_config['ldap_at_uid']
                    , at_allow_use = org_config['ldap_at_allow_use']
                    , at_pnumber = org_config['ldap_at_pnumber']
                    , at_email = org_config['ldap_at_email']
                    , at_username = org_config['ldap_at_username']
                    , at_dn = org_config['ldap_at_dn']
                    , at_ou = org_config['ldap_at_ou'])
            
            for all in uldap.get_all():
                ouinfo =  ou[1]
                dn = str(ou[0])
                ous.append( {'ou':ouinfo['ou'], 'dn':dn} )
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get ldap users')

        return ws_io.ws_output(dict(rt=rt.eid, ous=ous))
        
    #}}}

#LDAP授权
class LdapUsersAllowUse:
    #{{{
    def POST(self):
        """
        input:
            sid: sesssion id
            uid0: uid1
            uid1: uid2
            ...
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION

            uldap = user_ldap.create_ldap( ip = org_config['ldap_host']
                    , port = org_config['ldap_port']
                    , base_dn = org_config['ldap_base_dn']
                    , user_dn = org_config['ldap_user_dn']
                    , pw = org_config['ldap_pw']
                    , at_uid = org_config['ldap_at_uid']
                    , at_allow_use = org_config['ldap_at_allow_use']
                    , at_pnumber = org_config['ldap_at_pnumber']
                    , at_email = org_config['ldap_at_email']
                    , at_username = org_config['ldap_at_username']
                    , at_dn = org_config['ldap_at_dn']
                    , at_ou = org_config['ldap_at_ou']
                    , at_job = org_config['ldap_at_job'])

            uids = []
            for uid in i.keys():
                if len(uid) > 3 and uid[:3] == 'uid':
                    u = uldap.get_uid_by_username(i[uid])
                    if u:
                        uids.append(u)
            if not uldap.users_allow_use( uids ):
                raise ecode.MOD_LDAP_ERROR

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('LdapUsersAllowUse')

        return ws_io.ws_output(dict(rt=rt.eid,username=i.keys(),uids=uids))
    #}}}

class UserInfo:
    #{{{
    def GET(self):
        """
        input:
            sid:
            uid:
        output:
            rt: error code
            devs:{"devs":}
        """
        rt = ecode.FAILED
        devs = []

        try:
            i = ws_io.ws_input(['sid','uid'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION

            devs = user_db.devs( i['uid'])

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get user list')

        return ws_io.ws_output(dict(rt=rt.eid,devs=devs))
    #}}}
    
class CheckPwdAndDevs:
    #{{{
    def GET(self):
        """
        input:
            sid:
            uid:
            pwd:
        output:
            rt: error code
            devs:
        """
        rt = ecode.FAILED
        dev = ''

        try:
            i = ws_io.ws_input(['sid','uid','pwd'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION
                
            #创建LDAP连接   
            uldap = user_ldap.create_ldap( ip = org_config['ldap_host']
                                                       , port = org_config['ldap_port']
                                                       , base_dn = org_config['ldap_base_dn']
                                                       , user_dn = org_config['ldap_user_dn']
                                                       , pw = org_config['ldap_pw']
                                                       , at_uid = org_config['ldap_at_uid']
                                                       ,at_allow_use = org_config['ldap_at_allow_use']
                                                       , at_pnumber = org_config['ldap_at_pnumber']
                                                      , at_email = org_config['ldap_at_email'])    
            
            if user_db.is_has_user(i['uid']):    #如果用户已经注册过直接去数据库严重密码
                if user_db.check_pw(i['uid'],sha.new(i['pwd']).hexdigest()):
                    dev_id = dev_db.get_dev_id_by_curuser(i['uid'])
                    dev = dev_db.get_static_info(dev_id,'model_number')
                else:
                    raise ecode.USER_AUTH
            else:
                if uldap.get_user(i['uid']):     #如果用户在ldap中存在，说明用户未注册，否则用户不存在
                    raise ecode.USER_UN_VERIFIED
                else:
                    raise ecode.USER_NOT_EXIST

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get user list')

        return ws_io.ws_output(dict(rt=rt.eid,dev=dev))
    #}}}


class UserLog:
    #{{{
    def GET(self):
        """
        input:
            sid:
            dev_id:
        output:
            rt: error code
            logs:[{},..]
        """
        rt = ecode.FAILED
        logs = []
        logtime={}

        try:
            i = ws_io.ws_input(['sid','dev_id'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

#            org_config = org.get_config()
#            if user != org_config['admin']:
#                raise ecode.NOT_PERMISSION

            uid=dev_db.get_cur_user(i['dev_id'])
            logs = log_db.get_logs(uid,i['dev_id'])
            
            #日志时间
            for log in logs:
                utime=int(log['t'])*0.001   #长整型转换为python可操作时间戳
                logging.error('t is : %s',utime)
                utimeArry=time.localtime(utime)
                logtime=time.strftime("%Y-%m-%d %H:%M:%S",utimeArry)
                log['t']=logtime

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get user log')

        return ws_io.ws_output(dict(rt=rt.eid,logs=logs))
    #}}}


class LdapSync:
    #{{{
    def POST(self):
        """
        input:
            sid:
            admin_pw:
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            org_config = org.get_config()
            if not i.has_key('admin_pw'):
                user = session_db.user.get_user( i['sid'], web.ctx.ip)
                if not user:
                    raise ecode.NOT_LOGIN

                if user != org_config['admin']:
                    if not admin_db.is_has_admin(user):
                        raise ecode.NOT_PERMISSION
            else:
                if i['admin_pw'] != org_config['admin_pw']:
                    raise ecode.NOT_PERMISSION

            org.sync_ldap_user()

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('sync_ldap_user')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}


class LdapSyncConfig:
    #{{{
    def POST(self):
        """
        input:
            sid: session id
            ldap_sync_cycle: 
        output:
            rt: error code
        """
        rt = ecode.FAILED
        sid = ''

        try:
            i = ws_io.ws_input(['sid','ldap_sync_cycle'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION

            kv_table = {}
            kv_table['ldap_sync_cycle'] = i['ldap_sync_cycle']

            if not org.update_config(kv_table):
                raise ecode.DB_OP

            #os.system('wcloud_ldap_sync_server.py stop "%s"'%(org_config('ldap_sync_pidfile')))
            #if i['ldap_sync_cycle'] > 0:
            #    if 0 != os.system('wcloud_ldap_sync_server.py start "%s"'%(config.get('org_config'))):
            #        raise ecode.START_LDAP_SYNC_SERV

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('set org ldap config')

        return ws_io.ws_output(dict(rt=rt.eid))


    def GET(self):
        """
        input:
            sid: session id
        output:
            rt: error code
            ldap_sync_cycle: ''
        """
        rt = ecode.FAILED
        ldap_sync_cycle = 0

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION

            ldap_sync_cycle = org_config['ldap_sync_cycle']

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get org ldap config info')

        return ws_io.ws_output(dict(rt=rt.eid,ldap_sync_cycle= ldap_sync_cycle))
    #}}}
class LdapAddUser:
    #{{{
    def POST(self):
        '''
        input:
            sid: session id
            dn:  the oudn of adduser
            pw:  the init pw of user
            email: email
            mobile: Y/N  at_allow_use
            username:
            pnumber: telephone
            title: at_job
        output:
            rt: error code
        '''
        rt = ecode.FAILED
        
        try:
                
            i = ws_io.ws_input(['sid','dn','pw','email','mobile','username','pnumber','title'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION

            uldap = user_ldap.create_ldap( ip = org_config['ldap_host']
                    , port = org_config['ldap_port']
                    , base_dn = org_config['ldap_base_dn']
                    , user_dn = org_config['ldap_user_dn']
                    , pw = org_config['ldap_pw']
                    , at_uid = org_config['ldap_at_uid']
                    , at_allow_use = org_config['ldap_at_allow_use']
                    , at_pnumber = org_config['ldap_at_pnumber']
                    , at_email = org_config['ldap_at_email'])

            if uldap.get_user(i['email']):
               raise ecode.USER_EXIST
            if uldap.is_has_pnumber(i['pnumber']):
               raise ecode.USER_EXIST
#             userdn = i['dn']+','+ org_config['ldap_base_dn']
            userdn = 'cn=%s,%s,'%(str(i['username']),str(i['dn']))+org_config['ldap_base_dn']
            u = uldap.add_user(userdn,i['pw'],i['email'],i['mobile'],i['pnumber'],i['username'],i['title'])
            if not u:
                raise ecode.WRITE_LDAP_FAIL
           
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('Ldap add user failed')

        return ws_io.ws_output(dict(rt=rt.eid))
            
    #}}}
    
class LdapDelUser:
    #{{{
    def POST(self):
        """
        input:
            sid:
            uid: the email of user 
        output:
            rt: error ecode
        """
        rt = ecode.FAILED
        rdata=''
        
        try:
                
            i = ws_io.ws_input(['sid','uid'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION

            uldap = user_ldap.create_ldap( ip = org_config['ldap_host']
                    , port = org_config['ldap_port']
                    , base_dn = org_config['ldap_base_dn']
                    , user_dn = org_config['ldap_user_dn']
                    , pw = org_config['ldap_pw']
                    , at_uid = org_config['ldap_at_uid']
                    , at_allow_use = org_config['ldap_at_allow_use']
                    , at_pnumber = org_config['ldap_at_pnumber']
                    , at_email = org_config['ldap_at_email'])

            if not uldap.get_user(i['uid']):
                raise ecode.USER_NOT_EXIST
           
            if user_db.is_has_user(i['uid']):
                user_db.del_user(i['uid'])
            dev_id = dev_db.get_dev_id_by_curuser(i['uid'])
            if dev_id != None:
                dev_db.del_dev(dev_id)
                 
            rdata = uldap.get_user(i['uid'])
            logging.error("rdata is : %s",rdata)
            if rdata:
                u = uldap.delete_user(rdata[0])
                if not u:
                    raise ecode.DEL_LDAP_FAIL  
           
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('Ldap delete user failed')

        return ws_io.ws_output(dict(rt=rt.eid,dn=rdata[0]))
    #}}}
    
class OrgLogo:
    #{{{
    def POST(self):
        """
        input:
            sid: session id
            logo_base64: img raw date base64 code
            img_type: [jpeg|png]
        output:
            rt: error code
        """
        rt = ecode.FAILED
        sid = ''

        try:
            i = ws_io.ws_input(['sid','img_type','logo_base64'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                raise ecode.NOT_PERMISSION

            if not org.set_logo( i['logo_base64'], i['img_type']):
                raise ecode.SAVE_ORG_LOGO

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('set org ldap config')

        return ws_io.ws_output(dict(rt=rt.eid))


    def GET(self):
        """
        input:
            sid: session id
        output:
            rt: error code
            logo_base64:
            img_type: 
        """
        rt = ecode.FAILED
        logo_base64 = ''
        img_type = ''

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION

            logo_base64, img_type = org.get_logo()

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get org ldap config info')

        return ws_io.ws_output(dict(rt=rt.eid,logo_base64=logo_base64,img_type=img_type))
    #}}}
class AddAdmin:
    #{{{
    def POST(self):
        """
        input:
            sid:
            uid: user id
            pw: password
            ou: the range of uid's right
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['uid','pw','sid','ou'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 
            
            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                raise ecode.NOT_PERMISSION
            
            admin_db.add_admin(i['uid'], sha.new(i['pw']).hexdigest(),i['ou'])
            
            
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('org add admin')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}
    
    
class AddUser:
    #{{{
    def POST(self):
        """
        input:
            sid:
            uid: user id
            pw: password
            email: email uid
            pnumber: telephone
            title:
            mobile: yes/no
            
            
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['uid','pw','sid','ou'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 
            
            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                raise ecode.NOT_PERMISSION
            
            admin_db.add_admin(i['uid'], sha.new(i['pw']).hexdigest(),i['ou'])
            
            
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('org add admin')

        return ws_io.ws_output(dict(rt=rt.eid))
    
    #}}}
    
 #轨迹信息存储和读取
class TraceLocInfo:
    #{{{
    #web端调用
    def GET(self):
        """
        input；
            sid:
            start:
            end:
            uid:
        output:
            rt:
            locinfo:{key:value,key:value}
        """
        
        rt = ecode.FAILED
        locinfo={}
        
        try:
            i = ws_io.ws_input(['uid','sid','start','end'])
#             i = ws_io.ws_input(['uid','sid','start','end'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 
            
            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            org_config = org.get_config()
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION
            #将时间字符串转化为时间戳
            if str(i['start'])!='':
                starttime = time.mktime(time.strptime(str(i['start']), '%Y-%m-%d %H:%M'))
            else:
                starttime = ''
            if str(i['end'])!='':
                endtime = time.mktime(time.strptime(str(i['end']), '%Y-%m-%d %H:%M'))
            else:
                endtime = ''
            locinfo = trace.get(i['uid'],starttime,endtime)
        
            rt = ecode.OK
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('TraceLocInfo get failed')  
        
        return ws_io.ws_output(dict(rt=rt.eid,locinfo=locinfo))

    #客户端调用
    def POST(self):
        """
        input:
            sid:
            uid:
            key:
            value:
        output:
            rt:
        """
        
        rt=ecodo.FAILED
        
        try:
            i = ws_io.ws_input(['sid','key','value'])
            if not i:
                raise ecode.WS_INPUT
            
            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN
            
            trace.set(user,i['key'],i['value'])
            
            rt=ecode.OK
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('TraceLocInfo post failed')  
        
        return ws_io.ws_output(dict(rt=rt.eid))
                
            
    
    #}}}

class SendCertification:
    #{{{
    #供加密模块调用
    def POST(self):
        """
        input:
            uid: 客户端采用dev_id向加密模块请求证书数据
            bid: business id
            encCertification:证书数据
            signCertification:签名证书
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['uid','bid','encCertification','signCertification'])
            if not i:
                raise ecode.WS_INPUT
            
            if not cert_db.add_cert(i['uid'],i['bid'],i['encCertification'],i['signCertification']):
                raise ecode.DB_OP
            logging.error("证书数据是：%s",i['signCertification'])
            
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('send certification')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}                       
            
class GetAllBaseStation:
    #web端调用
    def GET(self):
        """
        input；
            sid: session id
            baseSec: org name
        output:
            rt: error code
            baseStationInfo: {baseStationID1: baseStation1,baseStationID2: baseStation2,...}
        """
        
        rt = ecode.FAILED
        baseStationInfo={}
        
        try:
            i = ws_io.ws_input(['sid','baseSec'])
            if not i:
                raise ecode.WS_INPUT
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP 
            
            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            #baseSec编码转换
            baseSec=i['baseSec'].encode('utf-8')
            temps=baseStation.get(baseSec)

            for temp in temps:
                baseStationInfo[temp[0]]=temp[1]
            
            if baseStationInfo == {}:
                logging.error('get baseStationInfo failed')
        
            rt = ecode.OK
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('baseStationInfo get failed')  
        
        return ws_io.ws_output(dict(rt=rt.eid,baseStationInfo=baseStationInfo))

