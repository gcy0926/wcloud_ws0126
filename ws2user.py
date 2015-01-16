# -*- coding: utf8 -*-

import web
import logging
import sha
import json
import user_db
import dev_db
import log_db
import session_db
import strategy_db
import ws_io
import ecode
import send_sms
import captcha_mng
import user_ldap
import org
import config
import time
import string
import user_ldap
import contact_db
import admin_db
import base_db
import trace
import re
import datetime
import math
##########################################
import shutil   #+++12.18
import os   #+++12.18
import commands   #+++12.18
import hashlib   #+++12.18





class Reg:
    #{{{
    def POST(self):
        """
        input:
            uid: user id
            cid: captcha id
            cvalue: captcha value
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['uid','cid','cvalue'])
            if not i:
                raise ecode.WS_INPUT

            org_config = org.get_config()
            if config.get('is_org') and org_config['auth_mode'] == org.AUTH_LDAP:
                raise ecode.UAUTH_NOT_ALLOW_OP

            if config.check_debug_acc( i['uid']) and i['cvalue'] == config.DEBUG_CVALUE:
                pass
            else:
                if not captcha_mng.check_captcha(i['cid'], i['cvalue']):
                    raise ecode.CAPTCHA_ERROR
            
            if not send_sms.check_pnumber( i['uid']) :
                raise ecode.ERROR_PNUMBER

            if user_db.is_verified( i['uid']) :
                raise ecode.USER_EXIST

            tmppw = config.make_pw()
            user_db.create( i['uid'], sha.new(tmppw).hexdigest() )

            send_sms.send_inital_pw( i['uid'], tmppw)

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('user reg.')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}


class Login:
    #{{{
    def POST(self):
        """
        input:
            uid: user id
            pw: password
            dev_id:
            IMSI: 
        output:
            rt: error code
            sid: session id
            need_mod_pw: need modify passwd
        """
        rt = ecode.FAILED
        sid = ''
        need_mod_pw = 0

        try:
            org_config = org.get_config()
            if config.get('is_org') and org_config['auth_mode'] == org.AUTH_LDAP:
                uldap = user_ldap.create_ldap( ip = org_config['ldap_host']
                                                       , port = org_config['ldap_port']
                                                       , base_dn = org_config['ldap_base_dn']
                                                       , user_dn = org_config['ldap_user_dn']
                                                       , pw = org_config['ldap_pw']
                                                       , at_uid = org_config['ldap_at_uid']
                                                       ,at_allow_use = org_config['ldap_at_allow_use']
                                                       , at_pnumber = org_config['ldap_at_pnumber']
                                                       , at_email = org_config['ldap_at_email'])

            i = ws_io.ws_input(['uid','pw','dev_id'])
            if not i:
                raise ecode.WS_INPUT
            #客户端登录
            if i['dev_id']!='web':
                # check password
                if not user_db.check_pw( i['uid'], sha.new(i['pw']).hexdigest()):
                    if user_db.is_has_user(i['uid']):
                        raise ecode.USER_AUTH
                    else:
                        if dev_db.is_has_dev(i['dev_id']):
                            raise ecode.NOT_PERMISSION
                        else:
                            if not uldap.check_pw( i['uid'], i['pw']):
                                raise ecode.USER_UN_REGISTER
                            
                            #+++12.22 待加一个判断，短信验证码的判断
                            
                            user_db.create( i['uid'], sha.new(i['pw']).hexdigest())
                            user_db.verified( i['uid']) 
                            user_db.pw_exp( i['uid'], False)
                            
                            user_db.add_dev( i['uid'], i['dev_id'])
                            dev_db.add_dev( i['dev_id'], i['uid'])
                            #把imsi存入user_db和dev_db中   +++12.16(change imsi)
                            #user_db.add_IMSI(i['uid'], i['IMSI'])
                            #dev_db.add_IMSI(i['dev_id'], i['IMSI'])
                            #把email存入user_db +++ 11.13(for 显示email)
                            contact = uldap.get_user(i['uid'])
                            info = contact[1]
                            email = ''
                            if info.has_key(org_config['ldap_at_email']):
                                email = info[org_config['ldap_at_email']]
                                if type(email) is list:
                                    email = email[0];
                            user_db.add_email(i['uid'], email)
                else:
                    if dev_db.get_cur_user(i['dev_id'])!=i['uid']:
                        raise ecode.NOT_PERMISSION  
                    if user_db.is_pw_exp( i['uid']):
                        need_mod_pw = 1
                    #读取最后一次上传的地理位置坐标和时间，写入文件中
                    loc = dev_db.get_loc(i['dev_id'])
                    upt = dev_db.get_last_update(i['dev_id'])
                    value = loc['lon']+":"+loc['lat']+":offline"
                    trace.set(i['uid'],upt,value)
                # create session
                sid = session_db.user.create( i['uid'], i['dev_id']
                        , web.ctx.ip)
                if not sid:
                    raise ecode.SDB_OP
                rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('user login')

        return ws_io.ws_output(dict(rt=rt.eid,sid=sid,need_mod_pw=need_mod_pw))
    #}}}

class SimVerify:
    #{{{
    def POST(self):
        """
        input:
            dev_id:
            IMSI: 
        output:
            rt: error code   0(换卡且卡已激活),52(换卡且卡未激活或卡未注册),其他(发生错误，请重试)
            sid: session id
        """
        rt = ecode.FAILED
        sid =''

        try:
            i = ws_io.ws_input(['dev_id','IMSI'])
            if not i:
                raise ecode.WS_INPUT
            
            cur_dev=dev_db.get_dev_by_IMSI(i['IMSI'])
            if not cur_dev==i['dev_id']:
                cur_user=dev_db.get_user_by_IMSI(i['IMSI'])
                if cur_user=='':
                    rt=ecode.USER_UNKNOWN_SIM
                else:
                    rt = ecode.OK
                    dev_db.change_dev(cur_user, i['IMSI'], i['dev_id'])
                    user_db.change_dev(cur_user, i['IMSI'], i['dev_id'])
                    #将策略改为未读
                    ids = dev_db.get_strategy_ids(cur_user)
                    for stra_id in ids:
                        if(str(stra_id['is_read'])== "true"):
                            stra_id['is_read']="false"
                    # create session
                    devId=dev_db.get_dev_id_by_curuser(cur_user)
                    sid = session_db.user.create(cur_user,devId,web.ctx.ip)
                    if not sid:
                        raise ecode.SDB_OP
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('sim_verify')

        return ws_io.ws_output(dict(rt=rt.eid,sid=sid))
    #}}}


class ForgetPW:
    #{{{
    def POST(self):
        """
        input:
            uid: 
            cid:
            cvalue:

        output:
            rt: error code
        """
        rt = ecode.FAILED
        try:
            i = ws_io.ws_input(['uid','cid','cvalue'])
            if not i:
                raise ecode.WS_INPUT

            org_config = org.get_config()
            if config.get('is_org') and org_config['auth_mode'] == org.AUTH_LDAP:
                raise ecode.UAUTH_NOT_ALLOW_OP

            if config.check_debug_acc( i['uid']) and i['cvalue'] == config.DEBUG_CVALUE:
                pass
            else:
                if not captcha_mng.check_captcha(i['cid'], i['cvalue']):
                    raise ecode.CAPTCHA_ERROR

            if not user_db.is_verified( i['uid']) :
                raise ecode.USER_NOT_EXIST

            tmppw = config.make_pw()
            user_db.set_pw( i['uid'], sha.new(tmppw).hexdigest() )
            user_db.pw_exp( i['uid'], True)
            send_sms.send_new_passwd( i['uid'], tmppw)

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('forgetpw')

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

            org_config = org.get_config()
            #if config.get('is_org') and org_config['auth_mode'] == org.AUTH_LDAP:
                #raise ecode.UAUTH_NOT_ALLOW_OP

            if not config.check_pw_rule( i['newpw']):
                raise ecode.PW_RULE

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            if not user_db.check_pw( user
                    , sha.new(i['oldpw']).hexdigest()):
                raise ecode.OLD_PW_ERROR

            user_db.set_pw( user, sha.new(i['newpw']).hexdigest())

            if user_db.is_pw_exp( user):
                user_db.pw_exp( user, False)

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('setpw')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}


class SendCmd:
    #{{{
    def POST(self):
        """
        input:
            sid:
            dev_id: 
            cmd:
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['cmd','dev_id','sid'])
            if not i:
                raise ecode.WS_INPUT

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP
            
            if admin_db.is_has_admin(user) or org.get_config()['admin'] == user:
                user = dev_db.get_cur_user( i['dev_id'])

            if not user_db.is_my_dev( user, i['dev_id']):
                raise ecode.NOT_PERMISSION

            dev_db.new_cmd( i['dev_id'], i['cmd'])

            dev_sid = session_db.user.get_sid( user, i['dev_id'])
            logging.error("dev_sid is : %s",dev_sid)

            config.notify_by_push_server(dev_sid,'cmd')

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('send cmd')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}
class SendCmdAndRs:
    #{{{
    def POST(self):
        """
        input:
            sid:
            dev_id: 
            cmd:
            flog:
            res:
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['cmd','dev_id','sid','res'])
            if not i:
                raise ecode.WS_INPUT

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

#             if config.get('is_org') and org.get_config()['admin'] == user:
#                 user = dev_db.get_cur_user( i['dev_id'])
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP
            
            if admin_db.is_has_admin(user) or org.get_config()['admin'] == user:
                user = dev_db.get_cur_user( i['dev_id'])
           
            if not user_db.is_my_dev( user, i['dev_id']):
                raise ecode.NOT_PERMISSION
            
            dev_sid = session_db.user.get_sid( user, i['dev_id'])
            
            dev_db.new_cmd_and_rs( i['dev_id'], i['cmd'],i['flog'],i['res'])
            
            config.notify_by_push_server(dev_sid,'cmd')   
           
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('send CmdAndRs')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}
# 设置设备管控命令标识位
class SetCmdRespons:
    #{{{
    def POST(self):
        """
        input:
            sid:
            info: wifi/bluetooth/tape
            results:  the respons
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['results','info','sid'])
            if not i:
                raise ecode.WS_INPUT

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            user,dev_id = session_db.user.get_user_and_dev( i['sid']
                    , web.ctx.ip)
            if not user_db.is_my_dev( user, dev_id):
                raise ecode.NOT_PERMISSION

            dev_db.set_rs( dev_id,i['info'],i['results'])

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('set cmd respons')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}
class GetCmdRespons:
    #{{{
    def GET(self):
        """
        input:
            sid:
            dev_id: 
            info: wifi/bluetooth/tape
        output:
            rt: error code
            rs:
        """
        rt = ecode.FAILED
        res = 0
        
        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT

            if i.has_key('dev_id'):
                dev_id = i['dev_id']
                user = session_db.user.get_user( i['sid'], web.ctx.ip)
            else:
                user,dev_id = session_db.user.get_user_and_dev( i['sid']
                        , web.ctx.ip)
            
            if not user:
                raise ecode.NOT_LOGIN

#             if config.get('is_org') and org.get_config()['admin'] == user:
#                 user = dev_db.get_cur_user( i['dev_id'])
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP
            
            if admin_db.is_has_admin(user) or org.get_config()['admin'] == user:
                user = dev_db.get_cur_user( i['dev_id'])
                
            if not user_db.is_my_dev( user, dev_id):
                raise ecode.NOT_PERMISSION

            res = dev_db.get_rs( dev_id,i['info'])

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get cmd respons')

        return ws_io.ws_output(dict(rt=rt.eid,res=res))
    #}}}
    
class SetallRespons:
    #{{{
    def POST(self):
        """
        input:
            sid:
            dev_id: 
            rs:  the respons
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['rs','dev_id','sid'])
            if not i:
                raise ecode.WS_INPUT

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

#             if config.get('is_org') and org.get_config()['admin'] == user:
#                 user = dev_db.get_cur_user( i['dev_id'])
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP
            
            if admin_db.is_has_admin(user) or org.get_config()['admin'] == user:
                user = dev_db.get_cur_user( i['dev_id'])

            if not user_db.is_my_dev( user, i['dev_id']):
                raise ecode.NOT_PERMISSION

            dev_db.set_all_rs( i['dev_id'],i['rs'])

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('set cmd respons')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}

class GetCmds:
    #{{{
    def GET(self):
        """
        input:
            sid:
            dev_id:
        output:
            rt: error code
            cmds: {...}
        """
        rt = ecode.FAILED
        cmds = {}

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT

            if i.has_key('dev_id'):
                dev_id = i['dev_id']
                user = session_db.user.get_user( i['sid'], web.ctx.ip)
            else:
                user,dev_id = session_db.user.get_user_and_dev( i['sid']
                        , web.ctx.ip)
            
            if not user:
                raise ecode.NOT_LOGIN

            if config.get('is_org') and org.get_config()['admin'] == user:
                user = dev_db.get_cur_user( i['dev_id'])

            if not user_db.is_my_dev( user, dev_id):
                raise ecode.NOT_PERMISSION

            cmds = dev_db.get_cmds( dev_id )
            for cmd in cmds:
                dev_db.complete_cmd(dev_id,cmd['id'])
            
            
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get cmds')

        return ws_io.ws_output(dict(rt=rt.eid,cmds=cmds))
    #}}}



class CompleteCmd:
    #{{{
    def POST(self):
        """
        input:
            sid:
            id:"cmd call id"
            results:
            info:
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['sid','id','results','info'])
            if not i:
                raise ecode.WS_INPUT

            user,dev_id = session_db.user.get_user_and_dev( i['sid']
                    , web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            if not user_db.is_my_dev( user, dev_id):
                raise ecode.NOT_PERMISSION

            dev_db.complete_cmd(dev_id, i['id'])

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('complete_cmd')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}
    
class GetStrategyById:
#{{{
   def GET(self):
       """
       input:
          sid:
          strategy_id:
       output:
          rt:error code
          strategy:{...}
       """
       rt = ecode.FAILED
       strategy = {}
       
       try:
            i = ws_io.ws_input(['sid','strategy_id'])
            if not i:
                raise ecode.WS_INPUT
            
            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            
            org_config = org.get_config()
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION
                         
            strategy_id = i['strategy_id']
            strategy = strategy_db.get_strategy_by_id(strategy_id)
            
            #如果是高级管理员，则加载所有作用人群
#             if user == org_config['admin']:
#                 strategys = strategy_db.get_strategys()
            #如果是单位管理员，则只需加载该单位的作用人群 
            if admin_db.is_has_admin(user):
                ou = admin_db.get_ou_by_uid(user)
                temp=[]
                rg = re.compile(r'.*'+ou+'.*')
                for us in strategy['users']:
                    if rg.match(us['name']):
                        temp.append(us)
                strategy['users'] = temp
           
            rt = ecode.OK
            
            
       except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get strategy by id')

       return ws_io.ws_output(dict(rt=rt.eid,strategy=strategy))

#}}}

class GetStrategyById1:
#{{{
   def GET(self):
       """
       input:
          sid:
          strategy_id:
       output:
          rt:error code
          strategy:{...}
       """
       rt = ecode.FAILED
       strategy = {}
       
       try:
            i = ws_io.ws_input(['sid','strategy_id'])
            if not i:
                raise ecode.WS_INPUT
            
            strategy_id = i['strategy_id']
            
            user,dev_id = session_db.user.get_user_and_dev( i['sid']
                    , web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN
#             if not user_db.is_my_dev( user, dev_id):
#                 raise ecode.NOT_PERMISSION
            
            #过去所有的下发了的策略
            strategy = strategy_db.get_strategy_by_id1(strategy_id)
#            将策略ID标志位写为已读 true
            dev_db.strategy_is_read(dev_id,strategy_id)
           
            rt = ecode.OK
            
       except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get strategy by id')

       return ws_io.ws_output(dict(rt=rt.eid,strategy=strategy))

#}}}

class GetStrategys:#
    #{{{
    def GET(self):
        """
        input:
            sid:这里的sid是什么意思
            
        output:
            rt: error code
            strategys: {...}
        """
        rt = ecode.FAILED
        strategys = {}

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN
            
            org_config = org.get_config()
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION
                
            #如果是高级管理员，则加载所有的策略
            if user == org_config['admin']:
                strategys = strategy_db.get_strategys()
            #如果是单位管理员，则只需加载作用为其单位人群的策略
            elif admin_db.is_has_admin(user):
                ou = admin_db.get_ou_by_uid(user)
                strategys = strategy_db.get_strategys_by_admin(ou) 
                #将策略的作用人群描述修改为在当前可管理范围内
                for strategy in strategys:
                    if len(strategy['userdesc'])>1:
                        temp=[]
                        rg = re.compile(r'.*'+ou+'.*')
                        for ud in strategy['userdesc']:
                            if rg.match(ud['name']):
                                temp.append(ud)
                                break
                        strategy['userdesc'] = temp
            rt = ecode.OK
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get strategys')

        return ws_io.ws_output(dict(rt=rt.eid,strategys=strategys))
    #}}}
    
class GetUserStrategys:#
    #{{{
    def GET(self):
        """
        input:
            sid:
            uid: for web only
        output:
            rt: error code
            strategys: {...}
        """
        rt = ecode.FAILED
        strategys = {}

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN
            
            org_config = org.get_config()
            
            #web端调用
            if user == org_config['admin'] or admin_db.is_has_admin(user):
                #user = dev_db.get_cur_user(i['dev_id'])
                ids = dev_db.get_strategy_ids(i['uid'])
                strategys = strategy_db.get_strategys_of_user_by_admin(ids)
            #客户端调用
            else:
                newids=[]
                ids = dev_db.get_strategy_ids(user)
                for stra_id in ids:
                    if(str(stra_id['is_read'])== "false"):
                        newids.append(stra_id)         
                strategys = strategy_db.get_strategys_to_user(newids)
                
                #判定策略是否时间有效，如果无效则删除dev数据库中相应的id号
                dev_id = dev_db.get_dev_id_by_curuser(user)
                key = time.time()
                for stra in strategys:
                    et = time.mktime(time.strptime(str(stra['end']), '%Y-%m-%d %H:%M'))
                    if et < key: #如果策略结束时间比当前服务器时间早，则视为无效数据，需要删除dev_id中的ID号
                        dev_db.complete_strategy(dev_id,stra['strategy_id'])
                #将读取后的id对应标记位 is_read设置为true
                logging.error(user)
                logging.error(dev_id)
                logging.error(len(newids))
                for strid in newids:
                    dev_db.strategy_is_read(dev_id,strid['strategy_id'])
#                     logging.error(strid['strategy_id'])
                    

            rt = ecode.OK
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get user strategys')

        return ws_io.ws_output(dict(rt=rt.eid,strategys=strategys))
    #}}} 
      
class GetUserNeedDelStrategys:#
    #{{{
    def GET(self):
        """
        input:
            sid:
            dev_id:
        output:
            rt: error code
            ids: [{"strategy_id": id}]
        """
        rt = ecode.FAILED
#         strategys = {}
        newids=[]
        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            user,dev_id = session_db.user.get_user_and_dev( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN
            
            ids = dev_db.get_strategy_ids(user)
            for stra_id in ids:
                if(str(stra_id['is_read'])== "delete"):
                     newids.append({"strategy_id":str(stra_id['strategy_id'])}) 
                     dev_db.complete_strategy(dev_id,str(stra_id['strategy_id']))       
#             strategys = strategy_db.get_strategys_to_user(newids)

            rt = ecode.OK
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get user need delete strategys')

        return ws_io.ws_output(dict(rt=rt.eid,ids=newids))
    #}}}  
class CompleteStrategy:
    #{{{
    def POST(self):
        """
        input:
            sid:
            id:"strategy call id"
            results:
            info:
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['sid','id','results','info'])
            if not i:
                raise ecode.WS_INPUT

            user,dev_id = session_db.user.get_user_and_dev( i['sid']
                    , web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            if not user_db.is_my_dev( user, dev_id):
                raise ecode.NOT_PERMISSION

#             dev_db.complete_strategy(dev_id, i['id'])
            #给strategy_id写入已读标记
            dev_db.strategy_is_read(dev_id,i['id'])

            rt = ecode.OK
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('complete_strategy')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}
    
class DeleteUserStrategy:
    #{{{
    def POST(self):
        """
        input:
            sid:
            id:   "strategy call id"
        output:
            rt:  error code 
        """
        
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['sid','id'])
            if not i:
                raise ecode.WS_INPUT

            user,dev_id = session_db.user.get_user_and_dev( i['sid']
                    , web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            if not user_db.is_my_dev( user, dev_id):
                raise ecode.NOT_PERMISSION

            dev_db.complete_strategy(dev_id, i['id'])

            rt = ecode.OK
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('delete_user_strategy')

        return ws_io.ws_output(dict(rt=rt.eid))
    
    #}}}   
    
class DeleteStrategy:
    #{{{
    def POST(self):
        """
        input:
            sid:
            id: "strategy call id"
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['sid','id'])
            if not i:
                raise ecode.WS_INPUT
            #user是管理员
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

            users = (strategy_db.get_strategy_by_id(i['id']))['users']
            strategy_db.del_strategy(i['id'])
            
            
            #dev_sid = session_db.user.get_sid( user, i['dev_id'])

            info='DelStrategy:'+str(i['id'])
           # config.notify_by_push_server(dev_sid,info)
           
            NotifyUsers(users,i['id'],info)

            rt = ecode.OK
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('delete_strategy')

        return ws_io.ws_output(dict(rt=rt.eid))
        
    #}}} 
#如果策略作用于多个单位，修改策略时将原有策略中该管理员单位的作用人群全部删除，然后重新建立一条策略...
class ModifyUsersofStrategy:
    #{{{
    def POST(self):
        """
        input
            id: strategy_id
            sid:
        output
            rt: error code
        """
        rt = ecode.FAILED
        
        try:
            i = ws_io.ws_input(['sid','id'])
            if not i:
                raise ecode.WS_INPUT
            user = session_db.user.get_user( i['sid'], str(web.ctx.ip))
            if not user:
                raise ecode.NOT_LOGIN
            org_config = org.get_config()
#             if user != org_config['admin']:
#                 raise ecode.NOT_PERMISSION
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION
                
                
            strategy = strategy_db.get_strategy_by_id(i['id'])
            ou = admin_db.get_ou_by_uid(user)
            
            rg = re.compile(r'.*'+ou+'.*')
            users = []
            delusers = []
            for us in strategy['users']:
                if not rg.match(us['name']):
                    users.append(us)
                else:
                    delusers.append(us)
                    
            userdesc = []
            for ud in strategy['userdesc']:
                if not rg.match(ud['name']):
                    userdesc.append(ud)                
            
            strategy_db.mod_users_of_strategy(i['id'],users,userdesc)
            
            info='DelStrategy:'+str(i['id'])
            NotifyUsers(delusers,i['id'],info)
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('Modify Users of Strategy ')
        return ws_io.ws_output(dict(rt=rt.eid))
            
    #}}}  
class ModifyStrategy:
    #{{{
    def POST(self):
        """
        input
            id:strategyID
            sid
                                开始时间 start
                                结束时间 end
                                作用经度 longitude 
                               作用维度 latitude
                                作用半径 radius
                                策略作用基站 baseStationID
                               范围描述  desc
  #                              摄像头 camera
                                蓝牙 bluetooth
            Wifi wifi
                                录音 tape
      #                          工作数据 data_work
                              作用人 users:{}
                             作用人描述userdesc:
        output
            rt: error code
        """
        rt = ecode.FAILED
        oldusers =[]
        try:
            i = ws_io.ws_input(['sid','id','users','userdesc','start','end','lon','lat','desc','radius','baseStationID','bluetooth','wifi','tape'])
            if not i:
                raise ecode.WS_INPUT
            strategy = {}
            """
            strategy={'end': '2014-03-12 08:00', 'wifi': 'wjy', 'lon': '12'
                      ,'bluetooth': 'bjy', 'start': '2014-03-11 08:00', 'camera': 'cfjy', 'radius': '10'
            ,'lat': '23'}
            """
            if str(i['start'])!='':
                strategy['start'] = str(i['start'])
                start = time.mktime(time.strptime(str(i['start']), '%Y-%m-%d %H:%M'))
            else:
                start = time.time()
                strategy['start'] = time.strftime('%Y-%m-%d %H:%M',time.localtime(start))#获取当前时间
            #如果前台传来时的时间是空的，那么开始时间取为当前时间，否则取为前台所选时间
            if str(i['end'])!='':
                strategy['end'] = str(i['end'])
            else:
                end = start+30*24*3600
                strategy['end'] = time.strftime('%Y-%m-%d %H:%M',time.localtime(end))
            """
            1、开始空，结束空 -----开始当前，结束当前加30天
            2、开始空，结束非空----开始当前，结束用传来的（已经默认前台传来的结束数据比当前时间晚）
            3、开始非空，结束空----开始用传来的，结束传来的加30天
            4、开始非空，结束非空--都用传来的
            """
            
            
            if str(i['lon'])=='':
                strategy['lon'] = '116.220686'
            else:
                strategy['lon']=str(i['lon'])
            if str(i['lat'])=='':
                strategy['lat'] = '39.979471'
            else:
                strategy['lat']=str(i['lat'])
            if str(i['radius'])=='':
                strategy['radius']='100'
            else:
                strategy['radius']=str(i['radius'])
            
            strategy['desc'] = i['desc']
 #           strategy['camera'] = str(i['camera'])
            strategy['bluetooth'] = str(i['bluetooth'])
            strategy['wifi'] = str(i['wifi'])
            strategy['tape'] = str(i['tape'])
  #          strategy['data_work'] = str(i['data_work'])
            strategy['strategy_id']=i['id']
            strategy['baseStationID']=i['baseStationID']
            
            user = session_db.user.get_user( i['sid'], str(web.ctx.ip))
            if not user:
                raise ecode.NOT_LOGIN
            
            org_config = org.get_config()
#             if user != org_config['admin']:
#                 raise ecode.NOT_PERMISSION
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION
            #将策略写入数据库strategy_db
            users=json.loads(i['users'])
            userdesc = json.loads(i['userdesc'])
            
            #获取策略原有的作用人群  
            stra = strategy_db.get_strategy_by_id(i['id'])
            oldusers=[]
            for im in stra['users']:
                for item in im['users']:
                    oldusers.append(item)
                    
            #修改策略内容
            strategy_db.mod_strategy(strategy,users,userdesc)
             
            
            #唤醒设备与pushsever之间的连接
            #dev_sid = session_db.user.get_sid( user, i['dev_id'])

            info='ModStrategy:'+str(i['id'])
            #config.notify_by_push_server(dev_sid,info)
            
            NotifyUsers(users,i['id'],info,oldusers)

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('modify strategy')
        return ws_io.ws_output(dict(rt=rt.eid))
    #}}} 
class SendStrategy:
    #{{{
    def POST(self):
        """
        input
             id:strategy id
             sid
                                开始时间 start
                                结束时间 end
                                作用经度 longitude 
                               作用维度 latitude
                                作用半径 radius
                                策略作用基站 baseStationID
                               范围描述  desc
    #                            摄像头 camera
                                蓝牙 bluetooth
             Wifi wifi
                                录音 tape
     #                           工作数据 data_work
                              作用人 users:{}
                             作用人描述userdesc:
        output
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['sid','id','users','userdesc','start','end','lon','lat','desc','radius','baseStationID','bluetooth','wifi','tape'])
            if not i:
                raise ecode.WS_INPUT
            strategy = {}
            
            if str(i['start'])!='':
                strategy['start'] = str(i['start'])
                start = time.mktime(time.strptime(str(i['start']), '%Y-%m-%d %H:%M'))
            else:
                start = time.time()
                strategy['start'] = time.strftime('%Y-%m-%d %H:%M',time.localtime(start))#获取当前时间
            #如果前台传来时的时间是空的，那么开始时间取为当前时间，否则取为前台所选时间
            if str(i['end'])!='':
                strategy['end'] = str(i['end'])
            else:
                end = start+30*24*3600
                strategy['end'] = time.strftime('%Y-%m-%d %H:%M',time.localtime(end))
            """
            1、开始空，结束空 -----开始当前，结束当前加30天
            2、开始空，结束非空----开始当前，结束用传来的（已经默认前台传来的结束数据比当前时间晚）
            3、开始非空，结束空----开始用传来的，结束传来的加30天
            4、开始非空，结束非空--都用传来的
            """ 
            if str(i['lon'])=='':
                strategy['lon'] = '116.220686'
            else:
                strategy['lon']=str(i['lon'])
            if str(i['lat'])=='':
                strategy['lat'] = '39.979471'
            else:
                strategy['lat']=str(i['lat'])
            if str(i['radius'])=='':
                strategy['radius']='100'
            else:
                strategy['radius']=str(i['radius'])
            strategy['baseStationID']=i['baseStationID']
            strategy['desc'] = i['desc']
  #          strategy['camera'] = str(i['camera'])
            strategy['bluetooth'] = str(i['bluetooth'])
            strategy['wifi'] = str(i['wifi'])
            strategy['tape'] = str(i['tape'])
 #           strategy['data_work'] = str(i['data_work'])
            strategy['strategy_id']=i['id']
            users=json.loads(i['users'])
            userdesc=json.loads(i['userdesc'])
            
            
            user = session_db.user.get_user( i['sid'], str(web.ctx.ip))
            if not user:
                raise ecode.NOT_LOGIN
            
            org_config = org.get_config()
            
            if user != org_config['admin']:
                if not admin_db.is_has_admin(user):
                    raise ecode.NOT_PERMISSION
            #将策略写入数据库strategy_db
            strategy_db.new_strategy(strategy,users,userdesc)
            
            #将策略ID写进dev-db中
            #唤醒设备与pushsever之间的连接

            info='NewStrategy:'+str(i['id'])
            #config.notify_by_push_server(dev_sid,info)
            NotifyUsers(users,i['id'],info)

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('send strategy')
        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}
    
class SendContacts:
    #{{{
    def POST(self):
        """
        input
            sid
            uid 接受方
            users:[uid1,uid2,...]联系人              
        output
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['sid','uid','users'])
            if not i:
                raise ecode.WS_INPUT
            users=json.loads(i['users'])
    
            user = session_db.user.get_user( i['sid'], str(web.ctx.ip))
            if not user:
                raise ecode.NOT_LOGIN

            contact_db.add_contact( i['uid'], users)
            
            dev_id = dev_db.get_dev_id_by_curuser(i['uid'])
            dev_sid = session_db.user.get_sid( i['uid'], dev_id)
            #在通知联系人列表有变化的同时要向用户数据库中写入刚刚发送的联系方式
            user_db.add_contact(i['uid'], users)
            #通知在线的设备联系人列表有变化
            config.notify_by_push_server(dev_sid,'contacts')

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('send contacts')
        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}
class GetContacts:#
    #{{{
    def GET(self):
        """
        input:
            sid:
        output:
            rt: error code
            contacts: [{name姓名,email电子邮件,job职位,department部门,pnumber电话号码}]
        """
        rt = ecode.FAILED
        contacts = []

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            logging.error("用户是:%s",user)
            if not user:
                raise ecode.NOT_LOGIN
            
            uids = user_db.get_contacts_by_uid(user)
            logging.error("用户的联系人信息:%s",str(uids))
            #清空联系人缓存区中的联系人信息
            user_db.del_contact(user)
            contacts = getLdapContact(uids)
            rt = ecode.OK
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get contacts')

        return ws_io.ws_output(dict(rt=rt.eid,contacts=contacts))
    #}}}
    
class DelContacts:#
    #{{{
    def POST(self):
        """
        input:
            sid:
            uid:
            contacts:[uids]
        output:
            rt: error code
#             contacts: [{name姓名,email电子邮件,job职位,department部门}]
        """
        rt = ecode.FAILED
        contacts = {}

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN
            
            uids = contact_db.get_contacts_by_uid(user);
            contacts = getLdapContact(uids) 

            rt = ecode.OK
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get contacts')

        return ws_io.ws_output(dict(rt=rt.eid,contacts=contacts))
    #}}}

def getLdapContact(uids):
    #{{{
    contacts = []
    org_config = org.get_config()
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
            
    for uid in uids:
        #uids是一个dic类  参数uid['uid']
        contact = uldap.get_user(uid['uid'])
        logging.error("ldap user:%s",str(contact))
        info = contact[1]
        dn = str(contact[0])
        if not dn:
            continue
        else:
            logging.error("dn:%s",dn)
            department = ''
            fenjie = dn.split(",");
            logging.error("fenjie:%s",str(fenjie))
            for son in fenjie:
                logging.error("son:%s",son)
                if son.find('ou')>=0:
                    department+=son[3:]+','
                else:
                    continue
            department = department[0:len(department)-1]

            uid = info[org_config['ldap_at_uid']]
            if type(uid) is list:
                uid = uid[0]
            
            username = ''
            if info.has_key(org_config['ldap_at_username']):
                username = info[org_config['ldap_at_username']]
                if type(username) is list:
                    username = username[0];
                                
            pnumber = ''
            if info.has_key(org_config['ldap_at_pnumber']):
                pnumber = info[org_config['ldap_at_pnumber']]
                if type(pnumber) is list:
                    pnumber = pnumber[0];
                    
            email = ''
            if info.has_key(org_config['ldap_at_email']):
                email = info[org_config['ldap_at_email']]
                if type(email) is list:
                    email = email[0];
                            
            job = ''
            if info.has_key(org_config['ldap_at_job']):
                job = info[org_config['ldap_at_job']]
                if type(job) is list:
                    job = job[0];
            one = {'name':username,'email':email,'job':job,'department':department,'pnumber':pnumber}
            contacts.append(one)
            
            
    return contacts
            
    #}}}
class Loc:
    #{{{
    def GET(self):
        """
        input:
            sid:
            dev_id:
        output:
            rt: error code
            lon:
            lat:
        """
        rt = ecode.FAILED
        lon = '0'
        lat = '0'
#         upt = '0'

        try:
            i = ws_io.ws_input(['sid','dev_id'])
            if not i:
                raise ecode.WS_INPUT

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            dev_id = i['dev_id']

            if not user:
                raise ecode.NOT_LOGIN

            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP
            #高级管理员可以定位单个设备的地理位置，单位管理则不可以
            #高级管理员
            if org.get_config()['admin'] == user:
                user = dev_db.get_cur_user( i['dev_id'])

                if not user_db.is_my_dev( user, dev_id):
                    raise ecode.NOT_PERMISSION

                loc = dev_db.get_loc( dev_id)
                lon = loc['lon']
                lat = loc['lat']
#                 upt = loc['upt']
            
            #单位管理员
            elif  admin_db.is_has_admin(user):
                user = dev_db.get_cur_user( i['dev_id'])

                if not user_db.is_my_dev( user, dev_id):
                    raise ecode.NOT_PERMISSION
                lon = " "
                lat = " "
#                 upt = " "
            else:
                raise ecode.NOT_PERMISSION

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('loc')

        return ws_io.ws_output(dict(rt=rt.eid,lon=lon,lat=lat))



    def POST(self):
        """
        input:
            sid:
            lon:
            lat:
            baseStationID: 基站地址
            offlinetime:客户端掉线的时间戳    毫秒级
            currenttime: 客户端当前的时间戳   毫秒级
            accuracy: 精度
        output:
            rt: error code
        处理的时间都是时间戳     秒级
        """
        rt = ecode.FAILED
        try:
            i = ws_io.ws_input(['lon','lat','sid'])
            if not i:
                raise ecode.WS_INPUT

            user,dev_id = session_db.user.get_user_and_dev( i['sid']
                    , web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            if not user_db.is_my_dev( user, dev_id):
                raise ecode.NOT_PERMISSION
#             如果坐标是小于零的数则表示定位失败  抛出异常，否则则正常存储
#             if float(i['lon'])<=0 or float(i['lon'])<=0:
#                 raise ecode.LOC_FAILED
#             else:
#            offset=服务器当前时间-客户端当前时间（key - i['onlinetime']）
            if i.has_key('baseStationId'):
                base_db.add_base(i['lon'],i['lat'],i['baseStationId'])
            item = trace.get_last_option(user)
            last_time = 0.0
            last_lon = 0.0
            last_lat = 0.0
            dis = 0.0
            key = time.time()
            if i['currenttime']!='':
                currenttime = int(i['currenttime'])/1000
            else:
                currenttime = key
#             if i.has_key('currenttime'):
#                 currenttime = int(i['currenttime'])/1000
#             else:
#                 currenttime = 
            dev_db.set_loc( dev_id, i['lon'], i['lat'])
#             value = i['lon']+':'+i['lat']+':yes:'+str(currenttime)+':'+str(int(key)-int(currenttime))
            value = i['lon']+':'+i['lat']+':online'
            
            offvalue = ''        
#                获取当前时间 %Y-%m-%d %H:%M
#                获取当前时间的时间戳 毫秒数
#                如果客户端没有长时间移动，则半个小时记录一次地理位置 
#                如果移动比较频繁，则是地理坐标超过500米则记录一次数据
            logging.error("user and item : %s , %s",user,item)
                
            if item: #获取section的最后一条记录的时间  有记录  ontime为客户端定位的时间
#                 last_lon,last_lat,status,ontime,offset = item[1].split(':')
                last_lon,last_lat,status = item[1].split(':')
                logging.error("old:"+str(item[0])+":"+str(item[1]))
                last_time = item[0]
                if status == "no": #如果上一条记录状态为离线，直接记录该条最新定位信息
                    trace.set(user,int(key),value)
                else:   #如果上一条记录状态为在线
                    if i['offlinetime']!='':#如果掉线时间不为空，即客户端重新上线  
                        offlinetime = int(i['offlinetime'])/1000
                        offvalue = last_lon+":"+last_lat+":offline"
                        offset = key - currenttime  #时间差为服务器当前时间和客户端上传时间之间的差值
                        trace.set(user,int(offlinetime+offset),offvalue)
                        trace.set(user,int(key),value)
                    else: #如果掉线时间为空，即客户端与上一次定位之间一直在线,记录当前最新定位信息    
                        dis = distance(i['lon'],i['lat'],last_lon,last_lat)
                        if float(last_lon)<=0.0 or float(last_lat)<=0.0:  #如果上一条记录定位失败的，
                            if float(i['lon'])>0 and float(i['lat'])>0:   #且 本次定位是成功的，则记录下该条信息
                                trace.set(user,int(key),value)
                        else: #如果上一次记录定位是成功的，则按时间和距离的规则来判定
                            if distance(i['lon'],i['lat'],last_lon,last_lat)>=500:
                                #如果两次记录的距离大于500米则记录
                                trace.set(user,int(key),value)
                            elif (float(key)-float(last_time))>= 30*60: #如果距离上次记录大于30分钟，则记录:
                                trace.set(user,int(key),value)
            else: #如果没有记录 记录下当前的时间及坐标即可
                trace.set(user,int(key),value)
            logging.error("new:"+str(key)+":"+value)
            logging.error("offline:"+i['offlinetime']+":"+offvalue)
#                 logging.error(last_time)
#                 logging.error(key)
#                 logging.error(last_lon)
#                 logging.error(last_lat)
            logging.error("distance:"+str(dis))
                
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('loc')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}

class GetLocAndCuruser:
    #{{{
    def GET(self):
        """
        input:
            sid:
            dev_id:
        output:
            rt: error code
            lon:
            lat:
        """
        rt = ecode.FAILED
        lon = '0'
        lat = '0'
        curuser=""

        try:
            i = ws_io.ws_input(['sid','dev_id'])
            if not i:
                raise ecode.WS_INPUT

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            dev_id = i['dev_id']

            if not user:
                raise ecode.NOT_LOGIN

#             if config.get('is_org') and org.get_config()['admin'] == user:
#                 user = dev_db.get_cur_user( i['dev_id'])
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP
            
            if admin_db.is_has_admin(user) or org.get_config()['admin'] == user:
                user = dev_db.get_cur_user( i['dev_id'])

            if not user_db.is_my_dev( user, dev_id):
                raise ecode.NOT_PERMISSION

            loc = dev_db.get_loc( dev_id)
            curuser = dev_db.get_cur_user(dev_id)
            lon = loc['lon']
            lat = loc['lat']

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('loc')
            
        return ws_io.ws_output(dict(rt=rt.eid,lon=lon,lat=lat,curuser=curuser))
        
    #}}}
    

class GetDevs:
    #{{{
    def GET(self):
        """
        input:
            sid:

        output:
            rt: error code
            devs: {...}
        """
        rt = ecode.FAILED
        devs = []

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            for dev in user_db.devs( user ):
                devs.append({'dev_id':dev
                    ,'model_number':dev_db.get_static_info(dev,'model_number')})

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get devs')

        return ws_io.ws_output(dict(rt=rt.eid,devs=devs))
    #}}}



class DelMe:
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

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            user_db.del_user( user )
            session_db.user.del_by_sid( i['sid'], web.ctx.ip)

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('del me')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}





class GetAccInfo:
    #{{{
    def GET(self):
        """
        input:
            sid: 

        output:
            rt: error code
            uid: 
        """
        rt = ecode.FAILED
        uid = ''

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT

            uid = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not uid:
                raise ecode.NOT_LOGIN

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('GetAccInfo')

        return ws_io.ws_output(dict(rt=rt.eid,uid=uid))
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



class GetOnlineStatus:
    #{{{
    def GET(self):
        """
        input:
            sid: 
            dev_id:
        output:
            rt: error code
            status: 0 not login, 1 login but offline, 2 online
        """
        rt = ecode.FAILED
        status = 0
        dev_sid=''

        try:
            i = ws_io.ws_input(['sid','dev_id'])
            if not i:
                raise ecode.WS_INPUT

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN
            
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP
            if admin_db.is_has_admin(user) or org.get_config()['admin'] == user:
                user = dev_db.get_cur_user( i['dev_id'])
            
            if not user_db.is_my_dev( user, i['dev_id']):
                raise ecode.NOT_PERMISSION

            dev_sid = session_db.user.get_sid( user, i['dev_id'])
            if dev_sid:
                status = 1
                if config.is_sid_on_push_server( dev_sid):
                    status = 2

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('GetOnlineStatus')

        return ws_io.ws_output(dict(rt=rt.eid, status=status,dev_sid=dev_sid))
    #}}}


class GetDevInfo:
    #{{{
    def GET(self):
        """
        input:
            sid: 
            dev_id:

        output:
            rt: error code
            last_update: 
        """
        rt = ecode.FAILED
        last_update = ''

        try:
            i = ws_io.ws_input(['sid','dev_id'])
            if not i:
                raise ecode.WS_INPUT

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP
            
            if admin_db.is_has_admin(user) or org.get_config()['admin'] == user:
                user = dev_db.get_cur_user( i['dev_id'])

            if not user_db.is_my_dev( user, i['dev_id']):
                raise ecode.NOT_PERMISSION

            last_update = dev_db.get_last_update( i['dev_id']) 

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('GetAccInfo')

        return ws_io.ws_output(dict(rt=rt.eid,last_update=last_update))
    #}}}


class DevStaticInfo:
    #{{{
    keys = ('firmware_version',
            'model_number',
            'version_number',
            'imei',
            'imei_version',
            'sim_supplier',
            'sim_sn',
            'sim_state',
            'signal_strength',
            'network_providers',
            'network_type',
            'phone_type',
            'call_status',
            'wifi_bssid',
            'wifi_ip_addr',
            'wifi_mac_addr',
            'wifi_rssi',
            'wifi_ssid',
            'wifi_network_id',
            'wifi_request_status',
            'wifi_conn_speed',
            'bluetooth_is_on',
            'bluetooth_is_search',
            'bluetooth_name',
            'bluetooth_addr',
            'bluetooth_status',
            'bluetooth_pair_dev',
            'battery_status',
            'battery_power',
            'battery_voltage',
            'battery_temperature',
            'battery_technology',
            'battery_life',
            'data_activity_status',
            'data_conn_status',
            'call_volume',
            'system_volume',
            'ring_volume',
            'music_volume',
            'tip_sound_volume',
            'longitude',
            'latitude',
            'pos_corrention_time')

    def GET(self):
        """
        input:
            sid: 
            dev_id:
            all:1
            key1:1
            key2:1
            ...

        output:
            rt: error code
            key1:value1
            key2:value2
            ...
        """
        rt = ecode.FAILED
        kv = {}

        try:
            i = ws_io.ws_input(['sid','dev_id'])
            if not i:
                raise ecode.WS_INPUT

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP
            
            if admin_db.is_has_admin(user) or org.get_config()['admin'] == user:
                user = dev_db.get_cur_user( i['dev_id'])

            if not user_db.is_my_dev( user, i['dev_id']):
                raise ecode.NOT_PERMISSION

            if i.has_key('all'):
                for k in self.keys:
                    kv[k] = dev_db.get_static_info( i['dev_id'], k)
            else:
                for k in i:
                    if k not in self.keys:
                        continue
                    kv[k] = dev_db.get_static_info( i['dev_id'], k)

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('DevStaticInfo')

        kv['rt'] = rt.eid
        return ws_io.ws_output(kv)


    def POST(self):
        """
        input:
            sid: 
            key1:value1
            key2:value2
            ...

        output:
            rt: error code
            count: update success count
        """
        rt = ecode.FAILED
        count = 0

        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT

            user,dev_id = session_db.user.get_user_and_dev( i['sid']
                    , web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            for k in i:
                if k not in self.keys:
                    continue
                dev_db.set_static_info( dev_id, k, i[k]) 
                count = count + 1

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('DevStaticInfo')

        return ws_io.ws_output(dict(rt=rt.eid,count=count))
    #}}}



class DevAppInfo:
    #{{{
    def GET(self):
        """
        input:
            sid: 
            dev_id:
        output:
            rt: error code
            apps: json([{},{}...])
        """
        rt = ecode.FAILED
        apps = ''
        not_install_apps = []

        try:
            i = ws_io.ws_input(['sid','dev_id'])
            if not i:
                raise ecode.WS_INPUT

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP
            
            if admin_db.is_has_admin(user) or org.get_config()['admin'] == user:
                user = dev_db.get_cur_user( i['dev_id'])

            if not user_db.is_my_dev( user, i['dev_id']):
                raise ecode.NOT_PERMISSION
            user = dev_db.get_cur_user(i['dev_id'])
            apps = dev_db.get_app_info( i['dev_id'])
            not_install_apps = user_db.get_apps( user )
            if apps:
                for a in json.loads(apps):
                    not_install_apps.remove(a['app_id'])

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('DevAppInfo')

        return ws_io.ws_output(dict(rt=rt.eid,apps=apps
            ,not_install_apps=not_install_apps))


    def POST(self):
        """
        input:
            sid: 
            apps: json([{},{}...])

        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['sid','apps'])
            if not i:
                raise ecode.WS_INPUT

            user,dev_id = session_db.user.get_user_and_dev( i['sid']
                    , web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            if i['apps']:
                for a in json.loads(i['apps']):
                    user_db.add_app( user, a['app_id'] )

            dev_db.set_app_info( dev_id, i['apps'])

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('DevAppInfo')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}



class DevWebAppInfo:
    #{{{
    def GET(self):
        """
        input:
            sid: 
            dev_id:

        output:
            rt: error code
            apps: json([{},{}...])
            not_install_apps: []
        """
        rt = ecode.FAILED
        apps = ''  
        not_install_apps = []

        try:
            i = ws_io.ws_input(['sid','dev_id'])
            if not i:
                raise ecode.WS_INPUT

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

#             if config.get('is_org') and org.get_config()['admin'] == user:
#                 user = dev_db.get_cur_user( i['dev_id'])
            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP
            
            if admin_db.is_has_admin(user) or org.get_config()['admin'] == user:
                user = dev_db.get_cur_user( i['dev_id'])

            if not user_db.is_my_dev( user, i['dev_id']):
                raise ecode.NOT_PERMISSION

            apps = dev_db.get_web_app_info( i['dev_id'])
            not_install_apps = user_db.get_web_apps( user )
            if apps:
                for a in json.loads(apps):
                    not_install_apps.remove(a['app_id'])

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('DevWebAppInfo')

        return ws_io.ws_output(dict(rt=rt.eid,apps=apps
            ,not_install_apps=not_install_apps))


    def POST(self):
        """
        input:
            sid: 
            apps: json([{},{}...])

        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['sid','apps'])
            if not i:
                raise ecode.WS_INPUT

            user,dev_id = session_db.user.get_user_and_dev( i['sid']
                    , web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            if i['apps']:
                for a in json.loads(i['apps']):
                    user_db.add_web_app( user, a['app_id'] )

            dev_db.set_web_app_info( dev_id, i['apps'])

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('DevWebAppInfo')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}


class Log:
    #{{{
    def POST(self):
        """
        input:
            sid:
            logs:json( [{t:"",app:"",act:"",info:""},{}..])
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['logs'])
            if not i:
                raise ecode.WS_INPUT

            user,dev_id = session_db.user.get_user_and_dev( i['sid']
                    , web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            for l in json.loads(i['logs']):
                log_db.add_log(user,dev_id,l['t'],l['app'],l['act'],l['info'])

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('log')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}
def NotifyUsers(users,strategy_id,info,oldusers=[]):
    for son in users:
        sonusers = son['users']
        for gson in sonusers:
            uid = gson['uid']
            dev_id = dev_db.get_dev_id_by_curuser(uid)
            if dev_id is None:
                continue
            else:
                dev_sid = session_db.user.get_sid( uid, dev_id)
                if((info.split(':'))[0]=='NewStrategy'): #
                    dev_db.add_strategy(dev_id,strategy_id)
#                     dev_sid = session_db.user.get_sid( uid, dev_id)
                    config.notify_by_push_server(dev_sid,info)
                elif((info.split(':'))[0]=='DelStrategy'):
                    #方案一    服务器无法判定客户端是否掉线
#                     #如果客户端不在线，给策略标志位写delete标识
#                     if not config.is_sid_on_push_server(dev_sid):
#                         dev_db.strategy_need_del(dev_id,strategy_id)
#                     #如果客户端在线，则直接删除相应策略id项
#                     if config.is_sid_on_push_server(dev_sid):
#                         dev_db.complete_strategy(dev_id,strategy_id)
                    #方案二
#                    无论客户端在线与否，都只对数据库里的标志位写delete标识，等客户端调用delete_user_strategy时再删除 
                    dev_db.strategy_need_del(dev_id,strategy_id)
                    config.notify_by_push_server(dev_sid,info)
                elif((info.split(':'))[0]=='ModStrategy'): 
                    if gson in oldusers: 
                    #如果在oldusers中存在 则给相应的客户端发送修改策略,并从oldusers中删除
                    #同时将dev中对应的策略标志位is_read 设置为false
                    #特殊情况  如果策略到期被删除以后，dev_db中的该策略ID将会被删除，此时再修改该策略就需要在dev_db中新加一条
                        if dev_db.is_has_strategy_id(dev_id,strategy_id):  #如果未改之前的策略未到期
                            dev_db.strategy_is_not_read(dev_id,strategy_id)
                        else: #如果未改之前的策略已到期
                            dev_db.add_strategy(dev_id,strategy_id)
#                         dev_sid = session_db.user.get_sid( uid, dev_id)
                        config.notify_by_push_server(dev_sid,info)
                        oldusers.remove(gson)
                    else:
                    #如果不在oldusers中，则说明其为新添加的用户，则发送新增策略，并在dev中写入策略编号
                        if dev_db.is_has_strategy_id(dev_id,strategy_id):
                            dev_db.strategy_is_not_read(dev_id,strategy_id)
                        else:
                            dev_db.add_strategy(dev_id,strategy_id)
#                         dev_sid = session_db.user.get_sid( uid, dev_id)
                        config.notify_by_push_server(dev_sid,'NewStrategy:'+strategy_id)
#                 continue                       
#                 dev_sid = session_db.user.get_sid( uid, dev_id)
#                 config.notify_by_push_server(dev_sid,info)
    
    #遍历oldusers oldusers剩下的就是从原有用户列表中删除的,则提醒用户删除该条策略，并删除dev中的策略ID           
    for ldu in oldusers:  
        
        dev_id1 =dev_db.get_dev_id_by_curuser(ldu['uid'])
        dev_sid1 = session_db.user.get_sid( ldu['uid'], dev_id1)
        
#         方案一：弊端服务器无法及时的判定客户端是否在线
        #如果不在线写标志位，让客户端上线后删除
#         if not config.is_sid_on_push_server(dev_sid1):
#             dev_db.strategy_need_del(dev_id1,strategy_id)
#         if config.is_sid_on_push_server(dev_sid1): #如果在线直接删除
#             dev_db.complete_strategy(dev_id1,strategy_id)
#         方案二：
#          服务器不判定客户端是否在线，都只是将标记位写上delete标识，等客户端下次上线以后去删除
        dev_db.strategy_need_del(dev_id1,strategy_id)
        config.notify_by_push_server(dev_sid1,'DelStrategy:'+strategy_id)

#计算两个经纬度之间的距离
def deg2rad(d):
    return float(d) * math.pi/ 180.0;
def distance(lon1,lat1,lon2,lat2): #经纬度
    radlat1=deg2rad(lat1)
    radlat2=deg2rad(lat2)
    a=radlat1-radlat2
    b=deg2rad(lon1)-deg2rad(lon2)
    s=2*math.asin(math.sqrt(math.pow(math.sin(a/2),2)+math.cos(radlat1)*math.cos(radlat2)*math.pow(math.sin(b/2),2)))
    earth_radius_meter = 6378137.0
#     s=round(s*earth_radius_meter,0)
    s = s*earth_radius_meter
    if s<0:
        return -s
    else:
        return s
                
                
                
                
class Test:
    #{{{
    def GET(self):
        """此方法是用于测试加解密的模块
        input:
            sid: 
            cryptograph:
        output:
            rt: error code
            age: []
            name:{}
        """
        i = ws_io.cws_input(['sid','cryptograph'])
        rt = ecode.FAILED
        age = [1,2,3]
        name = {'a':'ddd','b':'nnnn'}

        
        return ws_io.cws_output(dict(rt=rt.eid,age=age
            ,name=name))
#}}}

class GetCmdsEncry:
    #{{{
    def GET(self):
        """
        input:
            sid:
            cryptograph:
        output:
            rt: error code
            cmds: {...}
        """
        rt = ecode.FAILED
        cmds = []
        dev_id=''

        try:
            i = ws_io.cws_input(['sid'])
            cmds = []
#             dev_id = '862769025344539'
            logging.error("decode output:%s",str(i))
            if not i:
                raise ecode.WS_INPUT
   
            if i.has_key('dev_id'):
                dev_id = i['dev_id']
                user = session_db.user.get_user( i['sid'], web.ctx.ip)
            else:
                user,dev_id = session_db.user.get_user_and_dev( i['sid']
                        , web.ctx.ip)
               
            if not user:
                raise ecode.NOT_LOGIN
   
            if not user_db.is_my_dev( user, dev_id):
                raise ecode.NOT_PERMISSION
   
            cmds = dev_db.get_cmds( dev_id )
            for cmd in cmds:
                dev_db.complete_cmd(dev_id,cmd['id'])
            
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get cmds Encry')
#         return ws_io.cws_output(dict(rt=rt,cmds=cmds))
        return ws_io.cws_output(dict(rt=rt.eid,cmds=cmds),dev_id)
    #}}}
    
class GetCmdsEncry1:
    #{{{
    def GET(self):
        """
        input:
            sid:
            cryptograph:
        output:
            rt: error code
            cmds: {...}
        """
        rt = ecode.FAILED
        cmds = []
        dev_id=''

        try:
            i = ws_io.cws_input(['sid'])
            cmds = [{  "cmd" : "url 11", "id" : 362 }]
            dev_id = '862769025344539'
            logging.error("decode output:%s",str(i))
#             if not i:
#                 raise ecode.WS_INPUT
#   
#             if i.has_key('dev_id'):
#                 dev_id = i['dev_id']
#                 user = session_db.user.get_user( i['sid'], web.ctx.ip)
#             else:
#                 user,dev_id = session_db.user.get_user_and_dev( i['sid']
#                         , web.ctx.ip)
#               
#             if not user:
#                 raise ecode.NOT_LOGIN
#   
#             if not user_db.is_my_dev( user, dev_id):
#                 raise ecode.NOT_PERMISSION
#   
#             cmds = dev_db.get_cmds( dev_id )
#             for cmd in cmds:
#                 dev_db.complete_cmd(dev_id,cmd['id'])
            
            
            rt = 0
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get cmds Encry')
        return ws_io.ws_output(dict(rt=rt,cmds=cmds))
#         return ws_io.cws_output(dict(rt=rt,cmds=cmds),dev_id)
    #}}}
    
class GetStrategyById1Encry:
#{{{
    def GET(self):
       """
       input:
          sid:
          strategy_id:
       output:
          rt:error code
          strategy:{...}
       """
       rt = ecode.FAILED
       strategy = {}
       
       try:
            i = ws_io.cws_input(['sid','strategy_id'])   #从数据库读取数据
            if not i:
                raise ecode.WS_INPUT
            
            strategy_id = i['strategy_id']
            
            user,dev_id = session_db.user.get_user_and_dev( i['sid']
                    , web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN
#             if not user_db.is_my_dev( user, dev_id):
#                 raise ecode.NOT_PERMISSION
            
            #通过strategy_id返回一条策略（strategy_db）
            strategy = strategy_db.get_strategy_by_id1(strategy_id)
#            将策略ID标志位写为已读 true(dev_db)
            dev_db.strategy_is_read(dev_id,strategy_id)
           
            rt = ecode.OK
            
       except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get strategy by id')

       return ws_io.cws_output(dict(rt=rt.eid,strategy=strategy),dev_id)
   
   
#通过设备ID(dev_id)获取单个用户的策略信息(移动客户端only)
class GetUserStrategysEncry:#
    #{{{
    def GET(self):
        """
        input:
            sid:
            dev_id:
        output:
            rt: error code
            strategys: {...}
        """
        rt = ecode.FAILED
        strategys = {}

        try:
            i = ws_io.cws_input(['sid'])   #数据库读明文数据
            if not i:
                raise ecode.WS_INPUT
            
            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN
            
            org_config = org.get_config()
            
            #web端调用（弃）需要管理员来调用
            if user == org_config['admin'] or admin_db.is_has_admin(user):
                user = dev_db.get_cur_user(i['dev_id'])
                ids = dev_db.get_strategy_ids(user)
                strategys = strategy_db.get_strategys_of_user_by_admin(ids)
            #客户端调用
            else:
                newids=[]
                ids = dev_db.get_strategy_ids(user)   #获取user的strategys id（dev_db）
                for stra_id in ids:
                    if(str(stra_id['is_read'])== "false"):   #得到未读取策略id数组
                        newids.append(stra_id)         
                strategys = strategy_db.get_strategys_to_user(newids)   #获取未读策略（strategy_db）
                
                #判定策略是否时间有效，如果无效则删除dev数据库中相应的id号
                dev_id = dev_db.get_dev_id_by_curuser(user)
                key = time.time()
                for stra in strategys:
                    et = time.mktime(time.strptime(str(stra['end']), '%Y-%m-%d %H:%M'))
                    if et < key: #如果策略结束时间比当前服务器时间早，则视为无效数据，需要删除dev_id中的ID号
                        dev_db.complete_strategy(dev_id,stra['strategy_id'])
                        
                #将读取后的id对应标记位 is_read设置为true
                logging.error(user)
                logging.error(dev_id)
                logging.error(len(newids))
                for strid in newids:   #把策略标志位设置为已读
                    dev_db.strategy_is_read(dev_id,strid['strategy_id'])
#                     logging.error(strid['strategy_id'])
                    

            rt = ecode.OK
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get user strategys')

        return ws_io.cws_output(dict(rt=rt.eid,strategys=strategys),dev_id)
    #}}} 
    
    
class GetContactsEncry:#
    #{{{
    def GET(self):
        """
        input:
            sid:
        output:
            rt: error code
            contacts: [{name姓名,email电子邮件,job职位,department部门,pnumber电话号码}]
        """
        rt = ecode.FAILED
        contacts = []

        try:
            i = ws_io.cws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            
            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            logging.error("用户是:%s",user)
            if not user:
                raise ecode.NOT_LOGIN
            
            uids = user_db.get_contacts_by_uid(user)   #从用户数据库中取得该用户的待下发联系人
            logging.error("用户的联系人信息:%s",str(uids))
            #清空联系人缓存区中的联系人信息
            user_db.del_contact(user)
            contacts = getLdapContact(uids)   #通过这些uid在ldap中取得详细联系人信息
            
            dev_id = dev_db.get_dev_id_by_curuser(user)
            rt = ecode.OK
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('get contacts')

        return ws_io.cws_output(dict(rt=rt.eid,contacts=contacts),dev_id)
    #}}}
     
class SendStaticinfo:
    #{{{
    def POST(self):
        """
        input:
            sid:
            dev_id: 
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['dev_id','sid'])
            if not i:
                raise ecode.WS_INPUT

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP
            
            if admin_db.is_has_admin(user) or org.get_config()['admin'] == user:
                user = dev_db.get_cur_user( i['dev_id'])

            if not user_db.is_my_dev( user, i['dev_id']):
                raise ecode.NOT_PERMISSION

            dev_sid = session_db.user.get_sid( user, i['dev_id'])

            config.notify_by_push_server(dev_sid,'refresh staticinfo')

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('send Staticinfo')

        return ws_io.ws_output(dict(rt=rt.eid))

#数据备份   #+++12.18
class DataBackup:
    def POST(self):
        """
        input:
            sid: for phonenumber
            dev_id: verify: one phone one person
            backuptime: (int)
            data_path: default path
            data_verify:"file:md5"
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['sid','dev_id','backuptime','data_path','data_verify'])
            if not i:
                raise ecode.WS_INPUT
            
            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP
            
            if admin_db.is_has_admin(user) or org.get_config()['admin'] == user:
                user = dev_db.get_cur_user( i['dev_id'])

            if not user_db.is_my_dev( user, i['dev_id']):
                raise ecode.NOT_PERMISSION
            
            #生成存储路径
            phonenumber=user
            backup_home='/home/wcloud/opt/org/backup/'   #存放备份的文件夹(先有backup)
            backup_home_1=os.path.join(backup_home,phonenumber)
            rt1 = commands.getstatusoutput( 'mkdir %s'%(backup_home_1))
            backup_home_2=os.path.join(backup_home_1,i['backuptime'])
            rt2=commands.getstatusoutput( 'mkdir %s'%(backup_home_2))
                
            #将文件放到生成的目录下
            data=i['data_path']
            data_verify=i['data_verify']
            dataverify=data_verify.split(':')
            filename=dataverify[0]
            shutil.copy2(data, os.path.join(backup_home_2,filename))

            #校验文件
            file_path=os.path.join(backup_home_2,filename)
            file_md5=open(file_path,'rb')
            f_content=file_md5.read()
            file_md5.close()
            fmd5=hashlib.md5(f_content)
            if fmd5.hexdigest()!=dataverify[1]:
                raise ecode.FAILED

            rt = ecode.OK
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('data backup')
            
        #通知手机端数据备份是否成功
        if rt.eid==0:
            info='backup_success'
        else:
            info='backup_failed'
        dev_sid = session_db.user.get_sid( user, i['dev_id'])
        config.notify_by_push_server(dev_sid,info)

        return ws_io.ws_output(dict(rt=rt.eid))

#数据恢复   #+++12.18
class GetDevData:
    def GET(self):
        """
        input:
            sid: for phonenumber
            dev_id: “目标设备id”
            filename: backupdata name 压缩包
            backuptime: 备份时间 (int)
        output:
            rt: error code
            PATH: [filepath,filemd5]
        """
        rt = ecode.FAILED
        PATH=[]

        try:
            i = ws_io.ws_input(['sid','dev_id','filename','backuptime'])
            if not i:
                raise ecode.WS_INPUT

            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP
            
            if admin_db.is_has_admin(user) or org.get_config()['admin'] == user:
                user = dev_db.get_cur_user( i['dev_id'])

            if not user_db.is_my_dev( user, i['dev_id']):
                raise ecode.NOT_PERMISSION

            #生成校验值 md5
            phonenumber=user
            backup_home='/home/wcloud/opt/org/backup'
            file_path=os.path.join(backup_home,phonenumber,i['backuptime'],i['filename'])
            file_md5=open(file_path,'rb')
            f_content=file_md5.read()
            file_md5.close()
            filemd5=hashlib.md5(f_content)
            #生成下载路径
            filepath=os.path.join('/backup',phonenumber,i['backuptime'],i['filename'])
            PATH=[filepath,filemd5.hexdigest()]

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('Get backup data')

        return ws_io.ws_output(dict(rt=rt.eid,PATH=PATH))



    