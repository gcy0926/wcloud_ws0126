# -*- coding: utf8 -*-


class ECode(Exception):
    eid = 0 
    desc = ''
    def __init__(self, eid, desc):
        self.eid = eid
        self.desc = desc

    def __str__(self):
        return repr(self.eid)


OK              = ECode(0, '正确')
FAILED          = ECode(1, '未知错误')
USER_AUTH       = ECode(2, '用户名或密码错误')
DB_OP           = ECode(3, '数据库操作失败')
SDB_OP          = ECode(4, 'Session数据库操作失败')
WS_INPUT        = ECode(5, '请求参数错误')
NOT_LOGIN       = ECode(6, '用户未登录')
NOT_PERMISSION  = ECode(7, '权限不足')
SESSION_INVALID = ECode(8, 'Session已失效')
EMAIL_CFG       = ECode(9, '邮箱配置错误')
NO_EMAIL_CFG    = ECode(10, '缺少邮箱配置')
EMAIL_ADD       = ECode(11, 'EMAIL地址错误')
USER_EXIST      = ECode(12, '用户已存在')
SEND_SMS        = ECode(15, '无法向目标发送SMS信息')
ERROR_PNUMBER   = ECode(16, '错误的手机号码')
USER_NOT_EXIST  = ECode(17, '用户不存在')
PW_RULE         = ECode(18, '密码不符合规则')
OLD_PW_ERROR    = ECode(19, '旧密码错误')
DATA_TYPE_ERROR = ECode(20, '数据类型错误')
DATA_LEN_ERROR  = ECode(21, '数据长度错误')
TOO_MANY_DEVS   = ECode(22, '此用户设备数据过多')
CAPTCHA_ERROR   = ECode(23, '验证码错误')
CREATE_CAPTHCA_FAIL = ECode(24, '创建验证码失败')
SMS_TEMP_ERROR  = ECode(25, '错误的短信模板')
SMS_REQ_API_ERROR  = ECode(26, '发送短信时出错')
SMS_API_RES_ERROR  = ECode(27, '发送短信响应的结果有错误')
NEED_CAPTCHA  = ECode(28, '需要验证码')
INIT_LDAP_SERV  = ECode(29, '连接或登录LDAP Server失败')
UAUTH_NOT_ALLOW_OP = ECode(30, '当前用户验证方式不允许此操作')
NOT_ALLOW_OP = ECode(31, '当前版本不允许此操作')
MOD_LDAP_ERROR = ECode(32, '修改LDAP中的数据时发生错误')
START_LDAP_SYNC_SERV = ECode(33, '开启自动同步LDAP失败')
SAVE_ORG_LOGO = ECode(34, '保存企业LOGO失败')
EXIST_APP       = ECode(36, '已存在同名APP')
NOT_EXIST_APP   = ECode(37, '不存在的APP')
EXIST_ORG       = ECode(38, '已存在同名组织')
NOT_EXIST_ORG   = ECode(39, '不存在的组织')
READ_LDAP_FAIL = ECode(40,'读取LDAP数据失败')
USER_UN_VERIFIED = ECode(41,'用户未在客户端激活')
WRITE_LDAP_FAIL = ECode(42,'写入LDAP数据失败')
DEL_LDAP_FAIL = ECode(43,'删除LDAP失败')
SECTION_NOT_EXIT = ECode(44,'文件中section不存在')
LOC_FAILED = ECode(45,'定位失败')
INIT_ENCRYPT_ERROR = ECode(46,'初始化加密机失败')
CRYPT_ERROR = ECode(47,'加密或解密失败')
FINALIZE_ENCRYPT_ERROR = ECode(48,'反初始化加密机失败')
LOAD_LIB_ERROR = ECode(49,'加载共享库失败')
DECRYPT_DATA_LOSS = ECode(50,'解密数据丢包')
USER_UN_REGISTER=ECode(51,'用户未注册')   #+++12.19
USER_UNKNOWN_SIM=ECode(52,'卡未激活或未注册')   #+++12.19