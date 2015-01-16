# -*- coding: utf8 -*-

import ldap
import ldap.modlist as modlist
import logging
import ecode
import sys

reload(sys)
sys.setdefaultencoding('utf-8')



def create_ldap(ip, port=389, base_dn='', user_dn='', pw=''
        , at_uid='', at_allow_use='', at_pnumber='', at_email='',at_username='',at_dn = '',at_ou = '',at_job=''):
    """create a ldap, connect and login"""
    try:
        lobj = ldap.open(ip, port)

        if user_dn and pw:
            lobj.simple_bind_s(user_dn, pw)

        return UserLDAP( lobj, base_dn, at_uid, at_allow_use, at_pnumber
                , at_email,at_username,at_dn,at_ou,at_job)

    except:
        logging.exception('create ldap' )
    raise ecode.INIT_LDAP_SERV



class UserLDAP:
    def __init__(self, lobj, base_dn, at_uid, at_allow_use, at_pnumber
            , at_email,at_username,at_dn, at_ou, at_job):
        self.lobj = lobj
        self.base_dn = base_dn
        self.at_uid = at_uid
        self.at_allow_use = at_allow_use   #mobile键
        self.at_pnumber = at_pnumber
        self.at_email = at_email
        self.at_username = at_username
        self.at_dn = at_dn
        self.at_ou = at_ou
        self.at_job = at_job


    def __del__(self):
        self.lobj.unbind_s()

    #for readonly
    def get_all_users(self):
        """get all users for the ldap server"""
        try:
            res_id = self.lobj.search( self.base_dn, ldap.SCOPE_SUBTREE
                    , '%s=*'%(self.at_uid), None)
            users = []
            while self.lobj:
                rtype,rdata = self.lobj.result(res_id, 0)
                if not rdata:
                    break
                users.append(rdata[0])

            return users
        except:
            logging.exception('create ldap' )
        raise ecode.READ_LDAP_FAIL
    
    
    def get_all_ous(self):
        """get all users for the ldap server"""
        #查找同一层级SCOPE_ONELEVEL
        #基于群组的dn查找 
        try:
            res_id = self.lobj.search( self.base_dn, ldap.SCOPE_ONELEVEL
                    , '%s=*'%(self.at_ou), None)
            ous = []
            while self.lobj:
                rtype,rdata = self.lobj.result(res_id, 0)
                if not rdata:
                    break
                ous.append(rdata[0])

            return ous
        except:
            logging.exception('create ldap' )
        raise ecode.READ_LDAP_FAIL
    
    
    def get_all_onelevel(self, oudn):
        """get all users and ous on one level for the ldap server"""
        #查找同一层级SCOPE_ONELEVEL
        #基于群组的dn查找 
        try:
            res_id = self.lobj.search( oudn, ldap.SCOPE_ONELEVEL
                    , 'objectClass=*', None)
            onelevel = []
            while self.lobj:
                rtype,rdata = self.lobj.result(res_id, 0)
                if not rdata:
                    break
                onelevel.append(rdata[0])
            return onelevel
        except:
            logging.exception('ldap onelevel' )
            raise ecode.READ_LDAP_FAIL
        finally:
            del self
        
    
    def get_all(self):
        """get all users and ous from the ldap server获取所有的用户和群组"""
        try:
            res_id = self.lobj.search( self.base_dn, ldap.SCOPE_ONELEVEL
                    , 'objectClass=*', None)
            all = []
            while self.lobj:
                rtype,rdata = self.lobj.result(res_id, 0)
                if not rdata:
                    break
                all.append(rdata[0])
            return all
        except:
            logging.exception('ldap all' )
        raise ecode.READ_LDAP_FAIL


    def get_user(self, userid):
        """get a user info from the ldap server"""
        try:
            res_id = self.lobj.search( self.base_dn, ldap.SCOPE_SUBTREE
                    , '%s=%s'%(self.at_uid,userid), None)
            rtype,rdata = self.lobj.result(res_id, 0)
        except:
            logging.exception('get_user, search user,user=%s', userid )
            raise ecode.READ_LDAP_FAIL

        if not rdata:
#             raise ecode.USER_NOT_EXIST  
              return []
        return rdata[0]

    def get_uid_by_username(self, username):
        """get a user info from the ldap server"""
        try:
            res_id = self.lobj.search(self.base_dn, ldap.SCOPE_SUBTREE
                    , '%s=%s'%(self.at_username,username), None)
            rtype,rdata = self.lobj.result(res_id, 0)
        except:
            logging.exception('get_uid_by_username, search user,user=%s', username )
            raise ecode.READ_LDAP_FAIL

        if not rdata : 
              return ''
        return rdata[0][1][self.at_uid][0]
    
    def is_has_pnumber(self,pnumber):
        """ the telephone numner was used  yes or no"""
        try:
            res_id = self.lobj.search( self.base_dn, ldap.SCOPE_SUBTREE
                    , '%s=%s'%(self.at_pnumber,pnumber), None)
            rtype,rdata = self.lobj.result(res_id, 0)
        except:
            logging.exception('is_has_pnumber failed ,pnumber=%s', pnumber )
            raise ecode.READ_LDAP_FAIL

        if not rdata:
#             raise ecode.USER_NOT_EXIST  
              return False
        return True
            

    def check_pw(self, userid, pw):
        udata = self.get_user(userid)
        try:
            self.lobj.simple_bind_s(udata[0], pw)
            return True
        except:
            logging.exception('check_pw, simple_bind_s' )
        return False


    def is_allow_use(self, userid):
        try:
            udata = self.get_user(userid)
            if type(udata[1][self.at_allow_use]) is list:
                return udata[1][self.at_allow_use][0] == 'Y'
            else:
                return udata[1][self.at_allow_use] == 'Y'
        except:
            pass
        return False


    #for writeable
    def users_allow_use(self, uids):
        try:
            for u in self.get_all_users():
                #取得mobile的键值
                if u[1].has_key(self.at_allow_use):
                    old = { self.at_allow_use: u[1][self.at_allow_use][0]}
                else:
                    old = { self.at_allow_use: ''}
                #如果u在uids中，则mobile键值设为Y，否则为N
                if u[1][self.at_uid][0] in uids:
                    new = { self.at_allow_use: 'Y'}
                else:
                    new = { self.at_allow_use: 'N'}

                if old != new:
                    ldif = modlist.modifyModlist(old,new) #修改LDAP数据库的对象项
                    self.lobj.modify_s( u[0], ldif)

            return True
        except:
            logging.exception('users_allow_use' )
        return False
    
    
    def add_user(self,user_dn='', user_pw=''
        , at_uid='', at_allow_use='', at_pnumber='',at_username='',at_job=''):
        try:
#             if self.get_user(at_username):
#                 raise ecode.LDAP_USER_EXIST
            attrs = {}
            attrs['objectClass'] = ['top','inetOrgPerson']
            attrs['cn'] = str(at_username)
            if str(at_username[1:]):
                attrs['sn'] = str(at_username[1:])
            else:
                 attrs['sn'] = "6"
            attrs['mobile'] = str(at_allow_use)
            attrs['mail'] = str(at_uid)
            attrs['title'] =str( at_job)
            attrs['telephoneNumber'] =str(at_pnumber)
            attrs['userPassword'] =str( user_pw)
            ldif = modlist.addModlist(attrs)
#             dn = 'cn= %s,'%(at_username)+user_dn
            self.lobj.add_s(user_dn,ldif)
             
            return True 
        except:
#             pass
            logging.exception(user_dn)
        return False
    
    
    def delete_user(self,user_dn):
         try:
             self.lobj.delete_s(user_dn)
             
             return True                     
         except:
            pass
         return False
