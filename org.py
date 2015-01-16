# -*- coding: utf8 -*-
#!/usr/bin/env python

import config
import logging

# auth mode
AUTH_DEF = 0
AUTH_LDAP = 1

org_def_config = {
        'auth_mode':AUTH_DEF
        ,'org_name':''
        ,'org_addr':''
        ,'admin':'admin'
        ,'admin_pw':'d033e22ae348aeb5660fc2140aec35850c4da997'
        ,'admin_pnumber':''
        ,'admin_email':''
        ,'ldap_host' : ''
        ,'ldap_port' :389
        ,'ldap_base_dn' :''
        ,'ldap_user_dn' :''
        ,'ldap_pw' :''
        ,'ldap_at_uid' :''
        ,'ldap_at_allow_use' :''
        ,'ldap_at_pnumber' :''
        ,'ldap_at_username' :''
        ,'ldap_at_ou':''
        ,'ldap_at_dn' :''
        ,'ldap_at_email' :''
        ,'ldap_at_job' :''
        ,'ldap_sync_cycle' : 0
        ,'ldap_sync_ws' : ''
        }

def get_config():
    """get org key value."""
    global org_def_config
    org_config = org_def_config

    # read config value
    import ConfigParser, os
    c = ConfigParser.ConfigParser()
    try:
        if not c.read( os.path.join( os.getenv('CONFIG_DIR'),'org.ini') ):
            raise
        if not c.has_section('ORG'):
            raise
        for item in c.items('ORG'):  #将配置文件中的数据赋值给org_config
            k = item[0]
            if org_config.has_key(k):
                tk = type(org_config[k])
                if tk is bool:
                    org_config[k] = c.getboolean('ORG', k)
                elif tk is int:
                    org_config[k] = c.getint('ORG', k)
                elif tk is str:
                    org_config[k] = c.get('ORG', k)
                elif tk is float:
                    org_config[k] = c.getfloat('ORG', k)
                else:
                    pass
    except:
        logging.exception("read org config")
        pass

    return org_config


def update_config( kv_table ):
    """set org key values."""

    import ConfigParser, os
    c = ConfigParser.ConfigParser()
    try:
        if c.read( os.path.join( os.getenv('CONFIG_DIR')
            ,'org.ini')) and c.has_section('ORG'):
            pass
        else:
            c.add_section('ORG')

        for k in kv_table.keys():
            c.set('ORG', k, kv_table[k])

        with open(os.path.join( os.getenv('CONFIG_DIR')
            , 'org.ini'), 'wb') as configfile:
            c.write(configfile)
    except:
        logging.exception("set org config")
        return False

    return True



def sync_ldap_user():
    org_config = get_config()
    import user_ldap
    uldap = user_ldap.create_ldap( ip = org_config['ldap_host']
            , port = org_config['ldap_port']
            , base_dn = org_config['ldap_base_dn']
            , user_dn = org_config['ldap_user_dn']
            , pw = org_config['ldap_pw']
            , at_uid = org_config['ldap_at_uid']
            , at_allow_use = org_config['ldap_at_allow_use']
            , at_pnumber = org_config['ldap_at_pnumber']
            , at_email = org_config['ldap_at_email']
            , at_username= org_config['ldap_at_username']
            ,at_dn = org_config['ldap_at_dn']
            ,at_ou = org_config['ldap_at_ou']
            ,at_job = org_config['ldap_at_job'])
            
    import user_db
    for u in user_db.user_list():
        if not uldap.is_allow_use(u['uid']):
            user_db.del_user(u['uid'])
            logging.warn('sync_ldap_user: del user:%s',u['uid'])



def set_logo( logo, img_type):
    import base64
    import os
    os.remove(os.path.join( os.getenv('CONFIG_DIR'), 'logo.jpg'))
    os.remove(os.path.join( os.getenv('CONFIG_DIR'), 'logo.png'))
    with open( os.path.join( os.getenv('CONFIG_DIR'), 'logo.%s'%(img_type))
            , 'w') as lf:
        lf.write(base64.standard_b64decode(logo))
    return True


def get_logo():
    import base64
    import os
    logofile = ''
    img_type = ''
    if os.access( os.path.join(  os.getenv('CONFIG_DIR'), 'logo.jpg'), os.R_OK):
        logofile = os.path.join( os.getenv('CONFIG_DIR'), 'logo.jpg')
        img_type = 'jpg'
    elif os.access( os.path.join(os.getenv('CONFIG_DIR'), 'logo.png'), os.R_OK):
        logofile = os.path.join( os.getenv('CONFIG_DIR'), 'logo.png')
        img_type = 'png'
    else:
        return '', ''

    with open(logofile) as fp:
        return base64.standard_b64encode(fp.read()), img_type

    return '', ''

