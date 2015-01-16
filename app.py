#!/usr/bin/env python
# -*- coding: utf8 -*-

import web
import ws2user
import ws2caps
import ws2org
import ws2appstore
import ws2addr
import ecode
import ws_io
import config


version = '2.0.1'

class Version:
    def GET(self):
        rt = ecode.OK
        return ws_io.ws_output(dict(rt=rt.eid
            ,version=version
            ,is_org=config.get('is_org')
            ,is_debug=config.get('is_debug')))

urls = ( 
        "/a/wp/version", Version,
        "/a/wp/user/reg", ws2user.Reg,   #弃用
        "/a/wp/user/login", ws2user.Login,
        "/a/wp/user/sim_verify", ws2user.SimVerify,   #+++12.16
        "/a/wp/user/logout", ws2user.Logout,
        "/a/wp/user/send_cmd", ws2user.SendCmd,
        "/a/wp/user/get_cmds", ws2user.GetCmds,
        "/a/wp/user/get_cmds_encry", ws2user.GetCmdsEncry,   #未启用
        "/a/wp/user/get_cmds_encry1", ws2user.GetCmdsEncry1,   #未启用
        "/a/wp/user/complete_cmd", ws2user.CompleteCmd,
        "/a/wp/user/send_staticinfo", ws2user.SendStaticinfo,   #+++10.27
        "/a/wp/user/send_cmd_and_rs", ws2user.SendCmdAndRs,
        "/a/wp/user/set_cmd_respons", ws2user.SetCmdRespons,
        "/a/wp/user/set_all_respons", ws2user.SetallRespons,
        "/a/wp/user/get_cmd_respons", ws2user.GetCmdRespons,
        "/a/wp/user/send_strategy", ws2user.SendStrategy,
        "/a/wp/user/get_strategys", ws2user.GetStrategys,
        "/a/wp/user/get_strategy_by_id1", ws2user.GetStrategyById1,
        "/a/wp/user/get_strategy_by_id1_encry", ws2user.GetStrategyById1Encry,   #+++未启用
        "/a/wp/user/get_strategy_by_id", ws2user.GetStrategyById,
        "/a/wp/user/get_user_strategys",ws2user.GetUserStrategys,
        "/a/wp/user/get_user_strategys_encry",ws2user.GetUserStrategysEncry,   #+++未启用
        "/a/wp/user/get_user_need_del_strategys",ws2user.GetUserNeedDelStrategys,
        "/a/wp/user/complete_strategy", ws2user.CompleteStrategy,
        "/a/wp/user/del_strategy", ws2user.DeleteStrategy,
        "/a/wp/user/del_user_strategy", ws2user.DeleteUserStrategy,
        "/a/wp/user/modify_users_of_strategy", ws2user.ModifyUsersofStrategy,
        "/a/wp/user/modify_strategy", ws2user.ModifyStrategy,
        "/a/wp/user/send_contacts",ws2user.SendContacts,
        "/a/wp/user/get_contacts",ws2user.GetContacts,
        "/a/wp/user/get_contacts_encry",ws2user.GetContactsEncry,   #+++（添加dev_id） 未启用
        "/a/wp/user/del_contacts",ws2user.DelContacts,
        "/a/wp/user/loc", ws2user.Loc,
        "/a/wp/user/loc_and_cur_user",ws2user.GetLocAndCuruser,   #未启用
        "/a/wp/user/get_devs", ws2user.GetDevs,
        "/a/wp/user/del_me", ws2user.DelMe,
        "/a/wp/user/forget_pw", ws2user.ForgetPW,   #未启用，但总结了
        "/a/wp/user/set_pw", ws2user.SetPW,
        "/a/wp/user/get_acc_info", ws2user.GetAccInfo,   #未启用，但总结了
        "/a/wp/user/get_dev_info", ws2user.GetDevInfo,
        "/a/wp/user/get_online_status", ws2user.GetOnlineStatus,
        "/a/wp/user/dev_static_info", ws2user.DevStaticInfo,
        "/a/wp/user/dev_app_info", ws2user.DevAppInfo,
        "/a/wp/user/dev_wapp_info", ws2user.DevWebAppInfo,   #已弃用
        "/a/wp/user/log", ws2user.Log,
        "/a/wp/user/data_backup", ws2user.DataBackup,   #+++12.18
        "/a/wp/user/get_dev_data", ws2user.GetDevData,   #+++12.18
        "/a/wp/user/test", ws2user.Test,   #不用总结，用于测试
        "/a/wp/caps/get", ws2caps.Get,   #弃用，不用总结
        "/a/wp/caps/check", ws2caps.Check,   #弃用，不用总结
        "/a/wp/org/login", ws2org.Login,
        "/a/wp/org/logout", ws2org.Logout,
        "/a/wp/org/set_pw", ws2org.SetPW,
        "/a/wp/org/add_admin", ws2org.AddAdmin,
        "/a/wp/org/org_info", ws2org.OrgInfo,
        "/a/wp/org/ldap_config", ws2org.LdapConfig,
        "/a/wp/org/ldap_users", ws2org.LdapUsers,
        "/a/wp/org/ldap_ous",ws2org.LdapOus,
        "/a/wp/org/ldap_onelevel",ws2org.LdapOneLevel,
        "/a/wp/org/ldap_tree",ws2org.LdapTree,
        "/a/wp/org/ldap_users_allow_use", ws2org.LdapUsersAllowUse,
        "/a/wp/org/user_info", ws2org.UserInfo,
        "/a/wp/org/checkpwd_and_devs", ws2org.CheckPwdAndDevs,
        "/a/wp/org/ldap_sync", ws2org.LdapSync,
        "/a/wp/org/ldap_sync_config", ws2org.LdapSyncConfig,
        "/a/wp/org/ldap_add_user", ws2org.LdapAddUser,
        "/a/wp/org/ldap_del_user", ws2org.LdapDelUser,
        "/a/wp/org/logo", ws2org.OrgLogo,   #未启用，但总结了
        "/a/wp/org/trace_loc_info", ws2org.TraceLocInfo,
        "/a/wp/org/user_log", ws2org.UserLog,   #改过  11.5
        "/a/wp/org/send_certification", ws2org.SendCertification,
        "/a/wp/org/get_all_baseStation", ws2org.GetAllBaseStation,   #+++10.27
        "/a/was/applist", ws2appstore.AppList,
        "/a/was/appslist", ws2appstore.GetAppList,
        "/a/was/appinfo", ws2appstore.AppInfo,   #改过  11.5
        "/a/was/add_native_app", ws2appstore.AddNativeApp,
        "/a/was/update_native_app", ws2appstore.UpdateNativeApp,
        "/a/was/add_web_app", ws2appstore.AddWebApp,   #弃用，不用总结
        "/a/was/update_web_app", ws2appstore.UpdateWebApp,   #弃用，不用总结
        "/a/was/del_app", ws2appstore.DelApp,
        "/a/was/send_app", ws2appstore.SendApp,
        "/a/was/get_app_addr", ws2appstore.GetAppAddr,
        "/a/wqs/orglist", ws2addr.OrgList,
        "/a/wqs/orgaddr", ws2addr.OrgAddr,
        "/a/wqs/add_org", ws2addr.AddOrg,
        "/a/wqs/del_org", ws2addr.DelOrg
        )





app = web.application(urls, globals())
application = app.wsgifunc()



