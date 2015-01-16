# -*- coding: utf8 -*-


import web
import ecode
import ws_io
import app_db
import dev_db
import session_db
import config
import logging
import shutil
import os
import apk_info
import admin_db
import org
import user_db
import json
import time   #+++10.30
import baseStation   #+++11.4


class AppList:
    #{{{
    def GET(self):
        """
        web端调用，获取所有的应用id，然后根据应用id获取应用信息
        input:
            sort: utime|name
            is_asc: yes|no
            start: 
            count:
            key: 查询关键字
        output:
            rt: error code
            applist: [app_id,app_id]
        """
        rt = ecode.FAILED
        applist = []

        try:
            i = ws_io.ws_input([])

            sortkey = 'utime'
            if i.has_key('sort') and i['sort'] == 'name':
                sortkey = 'app_name'

            asc = 1
            if i.has_key('is_asc') and i['is_asc'] == 'no':
                asc = -1

            start = 0
            if i.has_key('start'):
                start = int(i['start'])

            count = 100
            if i.has_key('count'):
                count = int(i['count'])

            key = ''
            if i.has_key('key'):
                key = i['key']

            applist = app_db.get_app_list(key, sortkey, asc, start, count)
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('app list.')

        return ws_io.ws_output(dict(rt=rt.eid,applist=applist))
    #}}}

class GetAppList:
    #{{{
    def GET(self):
        """
                客户端调用，获取所有的应用id，然后根据应用id获取应用信息
        input:
            sort: utime|name
            is_asc: yes|no
            start: 
            count:
            key: 查询关键字
        output:
            rt: error code
            applist: [{},{}]
        """
        rt = ecode.FAILED
        applist = []

        try:
            i = ws_io.ws_input([])

            sortkey = 'utime'
            if i.has_key('sort') and i['sort'] == 'name':
                sortkey = 'app_name'

            asc = 1
            if i.has_key('is_asc') and i['is_asc'] == 'no':
                asc = -1

            start = 0
            if i.has_key('start'):
                start = int(i['start'])

            count = 100
            if i.has_key('count'):
                count = int(i['count'])

            key = ''
            if i.has_key('key'):
                key = i['key']

            applist = app_db.get_apps_list(key, sortkey, asc, start, count)
            logging.error('app list.=%s',applist)
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('客户端app list.')

        return ws_io.ws_output(dict(rt=rt.eid,applist=applist))
    #}}}
    

class AppInfo:
    #{{{
    def GET(self):
        """
        input:
            app_id:
        output:
            rt: error code
            appinfo: {}
            updatetime:{'year':'','month':'','day':''}
        """
        rt = ecode.FAILED
        appinfo = {}
        updatetime={}

        try:
            i = ws_io.ws_input(['app_id'])
            if not i:
                raise ecode.WS_INPUT

            appinfo = app_db.get(i['app_id'])
            
            #返回更新时间
            utime=int(appinfo['utime'])
            utimeArry=time.localtime(utime)
            updatetime['year']=utimeArry.tm_year
            updatetime['month']=utimeArry.tm_mon
            updatetime['day']=utimeArry.tm_mday
            
            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('app info.')

        return ws_io.ws_output(dict(rt=rt.eid,appinfo=appinfo,updatetime=updatetime))
    #}}}


class AddNativeApp:
    #{{{
    def POST(self):
        """
        input:
            apk_path:
            remark:
            apptype:
        output:
            rt: error code
            app_id:
        """
        rt = ecode.FAILED
        app_id = ''

        try:
            i = ws_io.ws_input(['apk_path','remark','apptype'])
            if not i:
                raise ecode.WS_INPUT

            ap = i['apk_path']
            ai = apk_info.get_apk_info( ap )
            logging.error('apkinfo%s', ai)
            appfile = "%s.apk"%(ai['app_id'])

            # copy apk file to web download dir.
            shutil.copy2(ap, os.path.join( config.get('app_download_dir'),'apps',appfile))

            app_db.add_app(ai['app_id'], ai['app_name'], i['apptype'], ai['version'],ai['versionCode'], '/apps/%s'%(appfile), i['remark'])
            app_id = ai['app_id']

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('add app')

        return ws_io.ws_output(dict(rt=rt.eid, app_id=app_id))
    #}}}


class UpdateNativeApp:
    #{{{
    def POST(self):
        """
        input:
            apk_path:
            remark:
            apptype:
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['apk_path','remark','apptype'])
            if not i:
                raise ecode.WS_INPUT

            ap = i['apk_path']
            ai = apk_info.get_apk_info( ap )
            appfile = "%s.apk"%(ai['app_id'])
            # copy apk file to web download dir.
            shutil.copy2(ap, os.path.join( config.get('app_download_dir'),'apps',appfile))

            app_db.update(ai['app_id'], ai['app_name'], i['apptype']
                    , ai['version'],ai['versionCode'],'/apps/%s'%(appfile), i['remark'])

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('update web app')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}

#弃用
class AddWebApp:
    #{{{
    def POST(self):
        """
        input:
            name:
            logo_base64:
            version:
            url:
            remark:
        output:
            rt: error code
            app_id:
        """
        rt = ecode.FAILED
        app_id = ''

        try:
            i = ws_io.ws_input(['name','logo_base64','version','url','remark'])
            if not i:
                raise ecode.WS_INPUT

            app_id = app_db.make_webapp_id()
            app_db.add_app(app_id, i['name'], 'web', i['logo_base64']
                    , i['version'], i['url'], i['remark'])

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('add web app')

        return ws_io.ws_output(dict(rt=rt.eid, app_id=app_id))
    #}}}

#弃用
class UpdateWebApp:
    #{{{
    def POST(self):
        """
        input:
            app_id:
            name:
            logo_base64:
            version:
            url:
            remark:
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['app_id','name','logo_base64','version','url','remark'])
            if not i:
                raise ecode.WS_INPUT

            app_db.update(i['app_id'], i['name'], 'web', i['logo_base64']
                    , i['version'], i['url'], i['remark'])

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('update web app')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}


class DelApp:
    #{{{
    def POST(self):
        """
        input:
            app_id:
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['app_id'])
            if not i:
                raise ecode.WS_INPUT

            app_db.del_app(i['app_id'])

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('del app')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}

class SendApp:
    #{{{
    def POST(self):
        """
                此接口的作用是向用户推送应用信息,
                输入数据是推送的应用id和需要推送的用户列表
        input:
            sid：身份验证
            app_ids:['app_id,versionCode','']
            users:[uid1,uid2,uid3]
        output:
            rt: error code
        """
        rt = ecode.FAILED

        try:
            i = ws_io.ws_input(['sid','users','app_ids'])
            logging.error(i)
            if not i:
                raise ecode.WS_INPUT
            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN

            if not config.get('is_org'):
                raise ecode.NOT_ALLOW_OP
            
            if not admin_db.is_has_admin(user) and not org.get_config()['admin'] == user:
                raise ecode.NOT_PERMISSION
            
            users=json.loads(i['users'])
            app_ids = json.loads(i['app_ids'])
            logging.error("app_ids :%s",app_ids)
            logging.error("i['app_ids'] :%s",i['app_ids'])
            
            #for system update   +++11.4
            temps=baseStation.get('updatesystem')
            for temp in temps:   #就一个
                if app_ids[0][0:22]==temp[0]:
                    newtemp=temp[0]+','+temp[1]
                    app_ids=[newtemp]
            logging.error("应用长度:%d",len(app_ids))
            #在每次向用户推送应用之前在用户数据表中写入缓存应用信息，要不然就只能向在线的用户推送应用了
            for uid in users:
                logging.error("uid:%s",uid)
                if len(user_db.devs(uid))==0:
                    continue
                else:
                    dev_id=user_db.devs(uid)[0]
                dev_sid = session_db.user.get_sid( uid, dev_id)
                
                logging.error("dev_sid:%s",dev_sid)
                #将app数组传入app_buffer中暂时存储
                user_db.add_app_buffer(uid,app_ids)
                
                info = 'apps'
                logging.error("notify info:%s",info)
                config.notify_by_push_server(dev_sid,info)

            rt = ecode.OK
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('send app')

        return ws_io.ws_output(dict(rt=rt.eid))
    #}}}
    

#     class SendApp:
#     #{{{
#     def POST(self):
#         """
#                 此接口的作用是向用户推送应用信息,
#                 输入数据是推送的应用id和需要推送的用户列表
#         input:
#             sid：身份验证
#             app_ids:['app_id,versionCode','']
#             users:[uid1,uid2,uid3]
#         output:
#             rt: error code
#         """
#         rt = ecode.FAILED
# 
#         try:
#             i = ws_io.ws_input(['sid','users','app_id','versionCode'])
#             logging.error(i)
#             if not i:
#                 raise ecode.WS_INPUT
#             user = session_db.user.get_user( i['sid'], web.ctx.ip)
#             if not user:
#                 raise ecode.NOT_LOGIN
# 
#             if not config.get('is_org'):
#                 raise ecode.NOT_ALLOW_OP
#             
#             if not admin_db.is_has_admin(user) and not org.get_config()['admin'] == user:
#                 raise ecode.NOT_PERMISSION
#             
#             logging.error("用户信息:%s",i['users'])
#             logging.error("应用信息:%s",i['app_id'])
#             logging.error("versionCode:%s",i['versionCode'])
#             
#             users=json.loads(i['users'])
#             #在每次向用户推送应用之前在用户数据表中写入缓存应用信息，要不然就只能向在线的用户推送应用了
#             for uid in users:
#                 logging.error("uid:%s",uid)
#                 if len(user_db.devs(uid))==0:
#                     continue
#                 else:
#                     dev_id=user_db.devs(uid)[0]
#                 dev_sid = session_db.user.get_sid( uid, dev_id)
#                 
#                 logging.error("dev_sid:%s",dev_sid)
# #                 user_db.add_app_buffer(uid,i['app_id']+':'+i['versionCode'])
#                 
#                 info = i['app_id']+':'+i['versionCode']
#                 logging.error("notify info:%s",info)
#                 config.notify_by_push_server(dev_sid,info)
# 
#             rt = ecode.OK
#         except Exception as e:
#             rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
#             logging.exception('send app')
# 
#         return ws_io.ws_output(dict(rt=rt.eid))
#     #}}}

class GetAppAddr:
    #{{{
    def GET(self):
        """
                此接口的作用是客户端根据收到的应用信息获取应用的下载地址，以下载应用
        input:
            sid：身份验证
        output:
            rt: error code
            apps:[{app_id,versionCode,url}]
        """
        rt = ecode.FAILED
        apps = []
        try:
            i = ws_io.ws_input(['sid'])
            if not i:
                raise ecode.WS_INPUT
            user = session_db.user.get_user( i['sid'], web.ctx.ip)
            if not user:
                raise ecode.NOT_LOGIN
            
            apps_sent = user_db.get_app_buffer(user)
            if apps_sent:
                for app_sent in apps_sent:
                    app_id = app_sent.split(',')[0]
                    versionCode = app_sent.split(',')[1]
                    logging.error('app_id is : %s, version code is : %s',app_id,versionCode)
                    #app = app_db.getapp(app_id,versionCode)
                    #apps.append(app)
                    user_db.del_app_buffer(user)
                    
                    #for system update   +++11.13
                    temps=baseStation.get('updatesystem')
                    for temp in temps:   #就一个
                        if app_id==temp[0]:
                            app={'app_id':app_id,'versionCode':versionCode,'url':'/update/com.singuloid.secphone.apk'}
                        else:
                            app = app_db.getapp(app_id,versionCode)
                        apps.append(app)
            
            rt = ecode.OK
            
        except Exception as e:
            rt = (type(e)==type(ecode.OK)) and e or ecode.FAILED
            logging.exception('GetAppAddr')

        return ws_io.ws_output(dict(rt=rt.eid,apps=apps))
    #}}}
