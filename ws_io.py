# -*- coding: utf8 -*-

# process web input and output 

import web
import json
import urlparse
import logging
import config
import string
import cert_db
import ecode
import session_db
import base64
from ctypes import *
import ctypes


def ws_input(want_list):
    i = web.input()
    logging.error("i:%s",i)
    for w in want_list:
        if not i.has_key(w):
            logging.error('web input error,need key:%s,raw input:%s',w,web.input())
            return None

    return i




def ws_output( outmap ):
    if config.get('is_debug'):
        logging.warn( 'DEBUG.req:%s %s', web.ctx.method, web.ctx.path)
        logging.warn( 'DEBUG.input:%s', web.input())
        logging.warn( 'DEBUG.output:%s', outmap)

    web.header('Content-Type', 'application/json')
    try:
        return json.dumps( outmap)
    except Exception,ex:
        logging.error('json dumps failed. ex:%s', ex)
        return ''


def cws_input(want_list):
    """
        现在客户端的加密方式是除了sid不加密，其余字段全部加密
    """
    i = web.input()
    
    #按照want_list对key对应的密文进行解密
    
    if i.has_key('cryptograph'):
        value,length = decrypt(i['sid'],i['cryptograph'])
        logging.error("decode result:%s",value)
        str = '{"sid"'+':'+i['sid']+','+value+'}'
        logging.error('whole str:%s',str)
        i = json.loads(str)
        if len(value)!=length:
            raise ecode.DECRYPT_DATA_LOSS
     
    for w in want_list:
        if not i.has_key(w):
            logging.error('web input error,need key:%s,raw input:%s',w,web.input())
            return None
        
#         return value
    
    return i

def decrypt( sid, cryptograph):
    """
        传入参数是一个密文字符串，是解密过程的一个抽象
    """
    
    #进行解密操作时要调用数据库中的方法来获取所需的参数
    """
    bEncryptedData, 密文串的数据
    uiEncryptedDataLen,密文串数据的长度
    derCert, 证书数据,这一项要求客户端在密文的外层还要加入客户端的dev_id，就是申请证书时的身份
    derCertLen, 证书数据的长度
    keyIndex,服务器证书的密钥号
    bOutData, 解密后的明文数据
    uiOutDataLen解密后的明文数据长度
    """
    #初始化解密模块
    so = cdll.LoadLibrary("./release/libDevoceControl.so")
    so._Z26InitDeviceControlInterfacev.argtypes = []
    so._Z26InitDeviceControlInterfacev.restype = c_int
    rt = so._Z26InitDeviceControlInterfacev()
    logging.error("init return:%d",rt)
    
    if rt:
        raise ecode.INIT_ENCRYPT_ERROR
    #声明参数类型
    so._Z20instructDecrpRequestPhjS_jiS_Pj.argtypes = [c_char_p,c_uint,c_char_p,c_uint,c_int,c_char_p,c_void_p]
    so._Z20instructDecrpRequestPhjS_jiS_Pj.restype = c_int
    
    bEncryptedData = cryptograph
    logging.error("cryptograph:%s",cryptograph)
    uiEncryptedDataLen = len(bEncryptedData)
    user,dev_id = session_db.user.get_user_and_dev( sid, web.ctx.ip)
#     dev_id = '862769025344539'
    logging.error("device:%s",dev_id)
    derCert = cert_db.get_signcert(dev_id)
    logging.error("signcert:%s",derCert)
    derCertLen = len(derCert)
    keyIndex = 1
    bOutData = create_string_buffer(500)
    #要求这一个要是字典型
    uiOutDataLen = c_uint(0) 
    
    rt = so._Z20instructDecrpRequestPhjS_jiS_Pj(bEncryptedData, uiEncryptedDataLen,
              derCert, derCertLen, keyIndex,bOutData, byref(uiOutDataLen))
    if rt:
        raise ecode.CRYPT_ERROR
    
    #反初始化
    if so._Z30FinalizeDeviceControlInterfacev():
        raise ecode.FINALIZE_ENCRYPT_ERROR
    return bOutData.value,uiOutDataLen.value



def cws_output( outmap,dev_id):
    
    
    if config.get('is_debug'):
        logging.warn( 'DEBUG.req:%s %s', web.ctx.method, web.ctx.path)
        logging.warn( 'DEBUG.input:%s', web.input())
        logging.warn( 'DEBUG.output:%s', outmap)
    web.header('Content-Type', 'application/json')
    try:
#         dev_id = "862769025344539"
        bEncryptedData,uiEncryptedDataLen = encrypt(outmap,dev_id)
        logging.error('encode output:%s', bEncryptedData)
        return json.dumps({'encryption':bEncryptedData,'len':uiEncryptedDataLen})
#         return json.dumps(dict(bEncryptedData=bEncryptedData))
#         return bEncryptedData
    except Exception,ex:
        logging.error('cws_output. ex:%s', ex)
        return ''
    
def encrypt(outmap,dev_id):
    #初始化接口
    so = cdll.LoadLibrary("./release/libDevoceControl.so")
    if not so:
        raise ecode.LOAD_LIB_ERROR
    rt = so._Z26InitDeviceControlInterfacev()
    logging.error("encode api init:%d",rt)
    if rt:
        raise ecode.INIT_ENCRYPT_ERROR
    
    #进行解密操作时要调用数据库中的方法来获取所需的参数
    """ 
    Src, 待加密的数据
    uisrcLen,待加密的数据长度
    derCert, 用户加密证书数据,这一项要求客户端在密文的外层还要加入客户端的dev_id，就是申请证书时的身份
    derCertLen, 加密证书数据的长度
    keyIndex,服务器证书的密钥号  默认为5
    bEncryptedData, 加密后的数据
    uiEncryptedDataLen,加密后的数据长度
    """
    
    #声明函数参数类型
    so._Z18instructCrpRequestPhjS_jiS_Pj.argtypes = [c_char_p,c_uint,c_char_p,c_uint,c_int,c_char_p,c_void_p]
    so._Z18instructCrpRequestPhjS_jiS_Pj.restype = c_int
    #将数据转换为符合json标准的str对象
#   Ssrc = json.dumps(outmap)
#     
#   Src = ''  
#   for key, value in outmap.items():
#       Src+= '"'+key+'"'+":"+'"'+str(value)+'"'+","
#   Src= Src[0:len(Src)-1]
#   Src="{"+Src+"}"
    Src1 = str(outmap)
    Src2 = Src1.replace('u\'','\"')
    Src = Src2.replace('\'','\"')
    logging.error("mingwen:%s",Src)
    uisrcLen = len(Src)
    logging.error("dev_id:%s",dev_id)
    derCert = cert_db.get_cert(dev_id)
    
#     derCert = "MIIBkjCCATigAwIBAgIDEX4lMAoGCCqBHM9VAYN1MDkxCzAJBgNVBAYTAkNOMSowKAYDVQQDDCHnp7vliqjkupLogZTnvZHlronlhajmnI3liqHlubPlj7AwHhcNMTQwNzA5MDYzMzQxWhcNMTUwNzA5MDYzMzQxWjA5MQswCQYDVQQGEwJDTjEqMCgGA1UEAwwhMjAxNDAzMjExMTM4MTMwMTIxNjg3QDE1MzIxOTc4Njg1MFkwEwYHKoZIzj0CAQYIKoEcz1UBgi0DQgAEPztLGItdSCbsQkBV3oimr7SqX0YSjio2UTQZHGqlTEisf+isJCnMy0WK2aTz9jJis3C3udInjlHMu16gwdha+6MvMC0wCwYDVR0PBAQDAgQwMBMGA1UdJQQMMAoGCCsGAQUFBwMBMAkGA1UdEwQCMAAwCgYIKoEcz1UBg3UDSAAwRQIgWq7m6DzoawiTilPqVWZipU86bwSqRAgJgyenesajcmsCIQC+omRTM1oyVvV2ACqdWUtO6Vg2Gts85VvSM0O8Xg/N0g=="; 
    derCertLen = len(derCert)
    keyIndex = 1
    bEncryptedData = create_string_buffer(1000)
    uiEncryptedDataLen = c_uint(0)
    
    #开始加密，获取返回值输出并验证
    encryrt = so._Z18instructCrpRequestPhjS_jiS_Pj(Src,uisrcLen,derCert,derCertLen,keyIndex,bEncryptedData,byref(uiEncryptedDataLen))
    
    if encryrt:
        raise ecode.CRYPT_ERROR
    finart = so._Z30FinalizeDeviceControlInterfacev()
    if finart:
        raise ecode.FINALIZE_ENCRYPT_ERROR
    return bEncryptedData.value,uiEncryptedDataLen.value





