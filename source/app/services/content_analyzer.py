"""SMS/Call Content Analysis Module"""
import re
from typing import Dict, Any, List
from loguru import logger


class ContentAnalyzer:
    """SMS and call content analyzer"""

    def __init__(self):
        # Fraud keyword library (extensively expanded with colloquial and common fraud scenarios)
        # NOTE: Keywords remain in Chinese as they are designed for Chinese-language content detection
        self.fraud_keywords = {
            "urgency": ["紧急", "立即", "马上", "尽快", "限时", "过期", "失效", "今天", "24小时", "抓紧", "赶紧", "立刻", "速度", "快快", "快"],
            "threat": ["逮捕", "起诉", "法院", "公安局", "刑侦", "通缉", "涉案", "涉嫌", "犯罪", "洗钱", "拘留", "传唤", "协查", "调查", "立案", "坐牢", "判刑", "死刑", "抓你", "抓人", "别挂", "不要挂", "别出声", "老实点", "后果自负"],
            "money": ["转账", "汇款", "安全账户", "验证码", "银行", "账户", "资金", "余额", "把钱转", "转到", "转入", "打钱", "交钱", "缴费", "借钱", "急用钱", "用钱", "款", "转钱", "转我", "转给", "给钱", "打款", "付钱", "付款", "收款", "转点", "发红包", "发钱", "拿钱", "凑钱", "垫付", "预付", "定金", "押金", "保证金", "手续费", "解冻费", "提现", "充值", "刷单"],
            "inducement": ["点击", "链接", "填写", "提供", "输入", "确认", "验证", "配合调查", "不方便", "不方便接电话", "下载", "安装", "扫码", "二维码", "注册", "实名", "认证", "共享屏幕", "屏幕共享", "远程协助", "发个验证码"],
            "impersonation": ["客服", "银行", "公安", "法院", "检察院", "社保", "税务", "通信", "工作人员", "警察", "警官", "法官", "检察官", "专案组", "经侦", "网警", "网安", "反诈中心", "银监局", "银保监", "中国移动", "中国联通", "中国电信", "京东", "淘宝", "支付宝", "微信", "抖音", "快手", "百万保障", "百万医疗"],
            "privacy": ["身份证号", "密码", "验证码", "银行卡号", "手机号", "个人信息", "身份证照片", "手持身份证", "银行卡密码", "支付密码", "登录密码", "交易密码", "CVV", "安全码", "背面的数字", "短信验证码", "人脸识别"],
            "relationship_fraud": ["我是你爹", "我是你妈", "我是你爸", "我是你哥", "我是你姐", "我是你弟", "我是领导", "我是老板", "我是老师", "我是同学", "我是朋友", "你儿子", "你女儿", "你老公", "你老婆", "你爷爷", "你奶奶", "出事了", "被抓了", "住院了", "出车祸", "进医院", "急需用钱", "快打钱", "别告诉", "别声张", "别让知道"],
            "investment": ["投资", "理财", "高回报", "稳赚", "保本", "收益", "日结", "日赚", "月入", "躺赚", "暴富", "内幕", "涨停", "牛股", "带单", "导师", "操盘", "数字货币", "区块链", "挖矿", "合约", "杠杆", "外汇", "期货", "原始股", "股权"],
            "fake_jobs": ["刷单", "佣金", "点赞", "关注", "兼职", "手工活", "打字员", "录入", "客服", "淘宝刷", "京东刷", "抖音点赞", "关注任务", "任务", "一单", "一任务", "返利", "返现"],
            "dating_fraud": ["裸聊", "约炮", "同城", "附近", "约会", "见面", "保证金", "诚意金", "私密", "激情", "视频", "直播间", "刷礼物", "送礼物"],
            "account_security": ["账号", "账户", "异常", "冻结", "停用", "限制", "锁定", "关闭", "注销", "失效", "过期", "被盗", "被盗刷", "风险", "安全提醒", "异地登录", "陌生设备"],
        }

        # Fraud pattern regex (extensively expanded)
        # NOTE: Patterns remain in Chinese as they are designed for Chinese-language content detection
        self.fraud_patterns = [
            r"安全账户",
            r"验证码",
            r"(转账|汇款|把钱转|转到|转入|转钱|转我|给钱|打钱).*(立即|马上|尽快|赶紧|立刻|现在|抓紧)",
            r"(涉嫌|参与|涉及).*(犯罪|洗钱|诈骗|非法|走私|毒品|案)",
            r"(公安局|法院|检察院|警察|警官).*电话",
            r"点击.*链接",
            r"(账户|账号).*(异常|冻结|停用|限制|锁定|关闭|注销|失效|过期|风险)",
            r"(积分|会员|VIP).*(兑换|过期|升级|到期|失效)",
            r"把钱转(到|给)",
            r"转到.*(账户|账号|卡|银行卡)",
            r"存在.*异常.*转",
            r"(领导|老板|朋友|同学|同事).*打钱",
            r"往.*卡里.*打.*钱",
            r"(领导|老板|老师).*(借钱|用钱|打款|急用|需要钱)",
            r"(换.*号|新.*号|换.*手机|新.*手机|换.*电话|新.*电话).*(打|转|给).*钱",
            r"(领导|老板|老师|同学|朋友|亲戚).*换.*号.*(打|转|给).*钱",
            r"(出事了|出车祸|住院|被抓).*钱",
            r"(儿子|女儿|老公|老婆|孙子|孙女|爷爷|奶奶).*(出事|被抓|住院|车祸|急用)",
            r"别告诉(家里|家人|父母|老公|老婆|孩子|任何人|别人)",
            r"(下载|安装).*(APP|应用|软件|程序|客户端)",
            r"(共享屏幕|屏幕共享|远程协助|远程控制)",
            r"(银行卡|信用卡|账户).*(冻结|被冻结|异常|风险|涉嫌)",
            r"转(\d+|[一二三四五六七八九十百千万亿]+)(块|元|r|R|钱)",
            r"给我转(\d+|[一二三四五六七八九十百千万亿]+)",
            r"借我(\d+|[一二三四五六七八九十百千万亿]+)",
            r"打(\d+|[一二三四五六七八九十百千万亿]+)(块|元|r|R|万|千)?(到|给|我)?",
            r"转(\d+|[一二三四五六七八九十百千万亿]+)(块|元|r|R|万|千)?(到|给|我)?",
            r"给(\d+|[一二三四五六七八九十百千万亿]+)(块|元|r|R|万|千)?",
            r"发(\d+|[一二三四五六七八九十百千万亿]+)(块|元|r|R|万|千)?",
            r"需要(\d+|[一二三四五六七八九十百千万亿]+)(块|元|r|R|万|千)?",
            r"急用(\d+|[一二三四五六七八九十百千万亿]+)(块|元|r|R|万|千)?",
            r"(百万保障|百万医疗|保险).*(过期|到期|关闭|取消|收费|扣费|续费)",
            r"(不配合|不处理|不解决).*(后果|责任|损失|承担)",
            r"(安全|保证金|押金|定金).*(退还|返还|退回|提现|解冻)",
            r"(刷单|刷信誉|刷流水).*(返利|返现|佣金|赚钱)",
            r"(导师|老师|专家|大师).*(带单|带赚|指导|操盘|内幕)",
            r"(稳赚|保本|高收益|高回报).*(投资|理财|项目)",
            r"(裸聊|视频).*(下载|APP|链接|邀请码)",
            r"(银行卡号|身份证|验证码|密码|支付密码).*(提供|输入|填写|发|发来|告诉我|给我)",
            r"(注销|取消|关闭).*(会员|VIP|保险|服务|业务|账户)",
            r"(帮你|可以帮你|能帮你|帮你解决|帮你处理).*(追回|退款|解冻|找回)",
            # More common fraud scripts
            r"(快递|包裹|邮件).*(问题|异常|扣留|海关|缴税|关税)",
            r"(社保|医保|公积金).*(异常|停用|冻结|违规|骗保)",
            r"(营业执照|企业执照|工商).*(异常|过期|年报|罚款)",
            r"(航班|机票|火车票).*(取消|改签|延误|退款|保险)",
            r"(学校|教育局|老师).*(学费|资料费|培训费|补课费)",
            r"(医院|医生|医保).*(手术费|医药费|住院费|押金)",
            r"(房东|中介|租房).*(押金|租金|中介费|看房费)",
            r"(游戏|账号|装备|皮肤).*(交易|购买|充值|解封|找回)",
            r"(微信|支付宝|支付).*(限额|风控|异常|解封|认证)",
            r"(手机|话费|流量|套餐).*(欠费|停机|充值|优惠|返现)",
            r"(信用卡|贷款|网贷|借款).*(提额|降息|免息|放款|手续费)",
            r"(股票|基金|证券|期货).*(内幕|消息|推荐|涨停|抄底)",
            r"(房产|房子|购房|租房).*(优惠|折扣|内部价|名额)",
            r"(汽车|买车|二手车|车贷).*(优惠|补贴|退税|保险)",
            r"(旅游|酒店|机票|签证).*(特价|优惠|退款|改签)",
            r"(招聘|工作|入职|面试).*(押金|培训费|体检费|服装费)",
            r"(考试|证书|资格证|学历).*(包过|保过|答案|改分|办证)",
            r"(保健品|药品|医疗器械).*(特效|根治|偏方|祖传)",
            r"(收藏品|古董|字画|邮票).*(鉴定|拍卖|收购|升值)",
            r"(彩票|赌博|赌球|棋牌).*(中奖|赢钱|返水|代理)",
            r"(风水|算命|占卜|星座).*(转运|改运|化解|法事)",
            r"(慈善|捐款|公益|救助).*(募捐|善款|资助|帮扶)",
            r"(黑客|黑客技术|盗号|破解).*(恢复|找回|解锁|入侵)",
            r"(代购|海外购|免税|海关).*(关税|清关|保证金|押金)",
            r"(微商|代理|加盟|分销).*(押金|货款|加盟费|培训费)",
            r"(相亲|交友|婚恋|红娘).*(会员费|见面费|礼物费|保证金)",
            r"(论文|代写|发表|期刊).*(定金|尾款|加急费|修改费)",
            r"(驾照|驾驶证|代考|包过).*(定金|尾款|关系费|打点费)",
            r"(护照|签证|移民|留学).*(中介费|加急费|保证金|押金)",
            r"(宠物|猫狗|买卖|领养).*(定金|运费|检疫费|疫苗费)",
            r"(装修|建材|家具|家电).*(定金|预付款|测量费|设计费)",
            r"(律师|法律|诉讼|维权).*(律师费|诉讼费|保证金|活动费)",
            r"(会计|审计|税务|代理记账).*(服务费|保证金|加急费)",
            r"(摄影|摄像|婚纱|写真).*(定金|尾款|选片费|修图费)",
            r"(健身|瑜伽|私教|课程).*(定金|课程费|私教费|器材费)",
            r"(美容|美发|整形|医美).*(定金|手术费|材料费|麻醉费)",
            r"(家政|保洁|保姆|月嫂).*(定金|中介费|服务费|保证金)",
            r"(维修|安装|清洗|疏通).*(上门费|材料费|加急费|保证金)",
            r"(搬家|运输|物流|快递).*(定金|运费|上楼费|包装费)",
            r"(开锁|换锁|配钥匙).*(上门费|开锁费|换锁费|材料费)",
            r"(回收|二手|闲置|转让).*(定金|检测费|运费|手续费)",
            r"(租赁|出租|共享).*(押金|租金|服务费|保证金)",
            r"(陪玩|陪聊|陪诊|陪护).*(定金|服务费|小费|保证金)",
            r"(跑腿|代驾|代购|代办).*(定金|服务费|加急费|小费)",
            r"(家教|辅导|培训|课程).*(定金|课时费|材料费|测试费)",
            r"(翻译|口译|笔译|同传).*(定金|翻译费|加急费|校对费)",
            r"(设计|策划|文案|创意).*(定金|设计费|策划费|修改费)",
            r"(编程|开发|网站|APP).*(定金|开发费|维护费|升级费)",
            r"(视频|直播|短视频).*(定金|制作费|推广费|流量费)",
            r"(音乐|作曲|编曲|录音).*(定金|制作费|版权费|混音费)",
            r"(绘画|插画|漫画|原画).*(定金|稿费|修改费|加急费)",
            r"(写作|小说|剧本|文案).*(定金|稿费|修改费|加急费)",
            r"(咨询|顾问|指导|教练).*(定金|咨询费|服务费|会员费)",
            r"(检测|鉴定|评估|认证).*(定金|检测费|报告费|加急费)",
            r"(保洁|清洗|消毒|除虫).*(定金|服务费|材料费|上门费)",
            r"(绿化|园艺|养护|修剪).*(定金|服务费|材料费|上门费)",
            r"(安保|保安|巡逻|监控).*(定金|服务费|器材费|安装费)",
            r"(物流|仓储|配送|运输).*(定金|运费|仓储费|装卸费)",
            r"(印刷|制作|广告|招牌).*(定金|制作费|安装费|设计费)",
            r"(服装|定制|裁缝|修改).*(定金|制作费|材料费|修改费)",
            r"(食品|餐饮|外卖|配送).*(定金|餐费|配送费|包装费)",
            r"(鲜花|礼品|蛋糕|定制).*(定金|制作费|配送费|包装费)",
            r"(婚庆|婚礼|婚宴|摄影).*(定金|策划费|场地费|服务费)",
            r"(庆典|活动|会议|展览).*(定金|策划费|场地费|服务费)",
            r"(团建|拓展|旅游|聚会).*(定金|活动费|交通费|住宿费)",
            r"(保险|理赔|投保|续保).*(定金|保费|手续费|服务费)",
            r"(银行|理财|存款|贷款).*(定金|手续费|服务费|管理费)",
            r"(证券|股票|基金|期货).*(定金|手续费|服务费|管理费)",
            r"(房产|中介|买卖|租赁).*(定金|中介费|服务费|评估费)",
            r"(汽车|买卖|租赁|维修).*(定金|中介费|服务费|检测费)",
            r"(教育|培训|学校|课程).*(定金|学费|材料费|考试费)",
            r"(医疗|医院|诊所|药品).*(定金|诊费|药费|检查费)",
            r"(法律|律师|诉讼|公证).*(定金|律师费|诉讼费|公证费)",
            r"(会计|税务|审计|代理).*(定金|服务费|代理费|咨询费)",
            r"(翻译|口译|笔译|同传).*(定金|翻译费|加急费|校对费)",
            r"(设计|策划|文案|创意).*(定金|设计费|策划费|修改费)",
            r"(编程|开发|网站|APP).*(定金|开发费|维护费|升级费)",
            r"(视频|直播|短视频).*(定金|制作费|推广费|流量费)",
            r"(音乐|作曲|编曲|录音).*(定金|制作费|版权费|混音费)",
            r"(绘画|插画|漫画|原画).*(定金|稿费|修改费|加急费)",
            r"(写作|小说|剧本|文案).*(定金|稿费|修改费|加急费)",
            r"(咨询|顾问|指导|教练).*(定金|咨询费|服务费|会员费)",
            r"(检测|鉴定|评估|认证).*(定金|检测费|报告费|加急费)",
            # Targeted fraud patterns
            r"(领导|老板|老师|主任|局长|处长|科长|经理|总监).*(换号|新号|新手机|新电话|新卡|新账户).*(打|转|给|汇).*钱",
            r"(领导|老板|老师|主任).*我是.*(小王|小李|小张|小刘|小陈).*换号.*打钱",
            r"(红包|发红包|抢红包).*(发|给|转|打).*(\d+|[一二三四五六七八九十百千万亿]+)",
            r"借.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千).*还",
            r"急需.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"救急.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"江湖救急.*(\d+|[一二三四五六七八九十百千万亿]+)",
            r"临时用.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"周转.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"垫付.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"先转.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千).*一会还",
            r"临时借.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"微信转.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"支付宝转.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"银行卡转.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"扫码支付.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"微信发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"支付宝发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"QQ发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"抖音发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"快手发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"微博发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"贴吧发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"论坛发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"群发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"私发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"私下发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"单独发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"个人发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"直接发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"马上发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"立即发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"赶紧发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"快点发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"速度发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"抓紧发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"尽快发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"急.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"紧急.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"救命.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"救人.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"救急.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"江湖救急.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"临时.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"周转.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"垫付.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"先发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千).*一会还",
            r"临时借.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"微信.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"支付宝.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"QQ.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"抖音.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"快手.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"微博.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"贴吧.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"论坛.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"群.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"私.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"私下.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"单独.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"个人.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"直接.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"马上.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"立即.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"赶紧.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"快点.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"速度.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"抓紧.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"尽快.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"急.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"紧急.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"救命.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"救人.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"救急.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"江湖救急.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"临时.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"周转.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"垫付.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
            r"先发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千).*一会还",
            r"临时借.*发.*(\d+|[一二三四五六七八九十百千万亿]+).*(块|元|r|R|万|千)",
        ]

    def analyze_content(self, content: str, content_type: str = "sms") -> Dict[str, Any]:
        """
        Analyze SMS or call content

        Args:
            content: Text content to analyze
            content_type: Content type (sms/call)

        Returns:
            Analysis result dict
        """
        try:
            result = {
                "content": content,
                "content_type": content_type,
                "risk_score": 0,
                "risk_level": "safe",
                "risk_factors": [],
                "fraud_category": None,
                "intent_analysis": {},
                "key_entities": []
            }

            # 1. Keyword analysis
            keyword_result = self._analyze_keywords(content)
            result["risk_score"] += keyword_result["score"]
            result["risk_factors"].extend(keyword_result["factors"])

            # 2. Pattern matching
            pattern_result = self._analyze_patterns(content)
            result["risk_score"] += pattern_result["score"]
            result["risk_factors"].extend(pattern_result["factors"])

            # 3. Emotion analysis (simplified)
            emotion_result = self._analyze_emotion(content)
            result["risk_score"] += emotion_result["score"]
            result["risk_factors"].extend(emotion_result["factors"])

            # 4. Entity extraction
            result["key_entities"] = self._extract_entities(content)

            # 5. Intent analysis
            result["intent_analysis"] = self._analyze_intent(content)

            # 6. Fraud classification
            result["fraud_category"] = self._classify_fraud_type(content, result["risk_factors"])

            # Normalize score
            result["risk_score"] = min(100, result["risk_score"])

            # Determine risk level
            result["risk_level"] = self._get_risk_level(result["risk_score"])

            logger.info(f"Content analysis completed: risk_score={result['risk_score']}, level={result['risk_level']}")
            return result

        except Exception as e:
            logger.error(f"Content analysis failed: {str(e)}")
            return {
                "content": content,
                "content_type": content_type,
                "risk_score": 50,
                "risk_level": "medium",
                "risk_factors": [f"Analysis error: {str(e)}"],
                "fraud_category": None,
                "intent_analysis": {},
                "key_entities": []
            }

    def _analyze_keywords(self, content: str) -> Dict[str, Any]:
        """Keyword analysis"""
        score = 0
        factors = []
        content_lower = content.lower()

        matched_categories = []
        all_matched_keywords = []

        for category, keywords in self.fraud_keywords.items():
            matched = [kw for kw in keywords if kw in content_lower]
            if matched:
                matched_categories.append(category)
                all_matched_keywords.extend(matched)
                # Different category weights
                weight = {
                    "threat": 15,
                    "money": 15,
                    "inducement": 12,
                    "impersonation": 15,
                    "privacy": 12,
                    "urgency": 8,
                    "relationship_fraud": 20,
                    "investment": 12,
                    "fake_jobs": 12,
                    "dating_fraud": 15,
                    "account_security": 10,
                }.get(category, 10)

                score += min(40, len(matched) * weight)

        # If multiple high-risk categories appear simultaneously, add bonus
        high_risk_categories = ["threat", "money", "impersonation", "relationship_fraud"]
        high_risk_count = sum(1 for cat in matched_categories if cat in high_risk_categories)
        if high_risk_count >= 2:
            score += 20
            factors.append(f"Detected {high_risk_count} high-risk category keywords simultaneously")

        if all_matched_keywords:
            factors.append(f"Found keywords: {', '.join(set(all_matched_keywords[:5]))}")

        return {"score": score, "factors": factors}

    def _analyze_patterns(self, content: str) -> Dict[str, Any]:
        """Pattern matching analysis"""
        score = 0
        factors = []

        for pattern in self.fraud_patterns:
            if re.search(pattern, content):
                score += 20
                factors.append(f"Matched fraud pattern: {pattern}")

        # Check for links
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        if urls:
            score += 15
            factors.append(f"Contains links: {len(urls)}")

        # Check for phone numbers
        phones = re.findall(r'1[3-9]\d{9}', content)
        if phones:
            score += 5
            factors.append(f"Contains phone numbers: {len(phones)}")

        # High-risk special case detection
        # 1. Boss changed number fraud
        leader_pattern = r'(领导|老板|老师|主任|局长|处长|科长|经理|总监).*(换号|新号|新手机|新电话|新卡|换手机|换电话).*(打|转|给|汇|需要|借|要).*(\d+|[一二三四五六七八九十百千万亿]+)'
        if re.search(leader_pattern, content):
            score += 50
            factors.append("Detected boss/number-change fraud pattern")

        # 2. Impersonating acquaintance fraud (I am your dad/mom/boss etc.)
        if re.search(r'我是(你爹|你妈|你爸|你哥|你姐|你弟|领导|老板|老师)', content) and re.search(r'(转|打|给|借).*(\d+|[一二三四五六七八九十百千万亿]+)', content):
            score += 50
            factors.append("Detected impersonating acquaintance fraud pattern")

        # 3. Emergency help fraud (urgent help needed, life-saving etc.)
        if re.search(r'(江湖救急|救命|救急|急需|急用).*(转|打|给|借).*(\d+|[一二三四五六七八九十百千万亿]+)', content):
            score += 30
            factors.append("Detected emergency help fraud pattern")

        # 4. Impersonating law enforcement (Public Security Bureau, Court etc. demanding transfer)
        if re.search(r'(公安|法院|检察院|警察|警官).*(转|打|给|汇).*钱', content):
            score += 60
            factors.append("Detected impersonating law enforcement fraud pattern")

        # 5. Impersonating customer service refund fraud
        if re.search(r'(客服|淘宝|京东|支付宝|微信).*(退款|退货|赔偿).*(转|打|给|提供)', content):
            score += 40
            factors.append("Detected impersonating customer service refund fraud pattern")

        return {"score": score, "factors": factors}

    def _analyze_emotion(self, content: str) -> Dict[str, Any]:
        """Emotion analysis (simplified)"""
        score = 0
        factors = []

        # Urgency
        urgency_words = ["立即", "马上", "尽快", "紧急", "限时", "今天", "24小时"]
        urgency_count = sum(1 for word in urgency_words if word in content)
        if urgency_count > 0:
            score += min(20, urgency_count * 10)
            factors.append("Content exhibits urgency characteristics")

        # Fear
        fear_words = ["逮捕", "起诉", "犯罪", "涉案", "冻结", "停用", "异常"]
        fear_count = sum(1 for word in fear_words if word in content)
        if fear_count > 0:
            score += min(25, fear_count * 12)
            factors.append("Content may induce panic")

        # Excessive exclamation marks
        exclamation_count = content.count('!') + content.count('！')
        if exclamation_count > 3:
            score += 10
            factors.append("Excessive use of exclamation marks")

        return {"score": score, "factors": factors}

    def _extract_entities(self, content: str) -> List[Dict[str, str]]:
        """Entity extraction"""
        entities = []

        # Extract URLs
        urls = re.findall(r'http[s]?://\S+', content)
        for url in urls:
            entities.append({"type": "url", "value": url})

        # Extract phone numbers
        phones = re.findall(r'1[3-9]\d{9}', content)
        for phone in phones:
            entities.append({"type": "phone", "value": phone})

        # Extract monetary amounts (supports multiple formats: 50r, 100块, 2万, 500元 etc.)
        amount_patterns = [
            r'(\d+\.?\d*)\s*(元|块|r|R)',
            r'(\d+\.?\d*)\s*(万|千|百)元?',
            r'(\d+\.?\d*)\s*万元',
            r'(\d+\.?\d*)\s*百万',
            r'转(\d+\.?\d*)(块|元|r|R|万|千)?',
            r'打(\d+\.?\d*)(块|元|r|R|万|千)?',
            r'给(\d+\.?\d*)(块|元|r|R|万|千)?',
            r'发(\d+\.?\d*)(块|元|r|R|万|千)?',
            r'借(\d+\.?\d*)(块|元|r|R|万|千)?',
            r'需要(\d+\.?\d*)(块|元|r|R|万|千)?',
            r'急用(\d+\.?\d*)(块|元|r|R|万|千)?',
            r'(\d+\.?\d*)\s*块钱',
            r'(\d+\.?\d*)\s*元钱',
        ]

        all_amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle tuple matches
                    num = match[0]
                    unit = match[1] if len(match) > 1 else ''
                    value = f"{num}{unit}"
                else:
                    # Handle single match
                    value = str(match)
                if value not in all_amounts:
                    all_amounts.append(value)
                    entities.append({"type": "amount", "value": value})

        # Extract bank card numbers
        bank_cards = re.findall(r'\d{16,19}', content)
        for card in bank_cards:
            entities.append({"type": "bank_card", "value": card})

        return entities

    def _analyze_intent(self, content: str) -> Dict[str, Any]:
        """Intent analysis"""
        intents = {
            "request_money": False,
            "request_info": False,
            "threaten": False,
            "impersonate": False,
            "create_urgency": False,
            "relationship_fraud": False,
            "investment_fraud": False,
            "shopping_fraud": False,
            "job_fraud": False,
            "dating_fraud": False,
        }

        content_lower = content.lower()

        # Request for money/transfer
        money_keywords = ["转账", "汇款", "转入", "安全账户", "转钱", "转我", "给钱", "打钱", "打款", "付钱", "付款", "收款", "转点", "发红包", "发钱", "拿钱", "凑钱", "垫付", "预付", "定金", "押金", "保证金", "手续费", "解冻费", "提现", "充值"]
        if any(word in content_lower for word in money_keywords):
            intents["request_money"] = True

        # Request for information
        info_keywords = ["验证码", "密码", "身份证号", "银行卡号", "身份证照片", "手持身份证", "银行卡密码", "支付密码", "登录密码", "交易密码", "CVV", "安全码", "背面的数字", "短信验证码", "人脸识别"]
        if any(word in content_lower for word in info_keywords):
            intents["request_info"] = True

        # Threaten
        threat_keywords = ["逮捕", "起诉", "犯罪", "法院", "公安", "拘留", "传唤", "协查", "调查", "立案", "坐牢", "判刑", "死刑", "抓你", "抓人", "别挂", "不要挂", "别出声", "老实点", "后果自负"]
        if any(word in content_lower for word in threat_keywords):
            intents["threaten"] = True

        # Impersonate
        impersonate_keywords = ["客服", "银行", "公安", "法院", "检察院", "社保", "税务", "通信", "工作人员", "警察", "警官", "法官", "检察官", "专案组", "经侦", "网警", "网安", "反诈中心", "银监局", "银保监", "中国移动", "中国联通", "中国电信", "京东", "淘宝", "支付宝", "微信", "抖音", "快手", "百万保障", "百万医疗"]
        if any(word in content_lower for word in impersonate_keywords):
            intents["impersonate"] = True

        # Create urgency
        urgency_keywords = ["立即", "马上", "紧急", "限时", "过期", "抓紧", "赶紧", "立刻", "速度", "快快", "快", "今天", "24小时", "尽快", "失效"]
        if any(word in content_lower for word in urgency_keywords):
            intents["create_urgency"] = True

        # Relationship fraud
        relationship_keywords = ["我是你爹", "我是你妈", "我是你爸", "我是你哥", "我是你姐", "我是你弟", "我是领导", "我是老板", "我是老师", "我是同学", "我是朋友", "你儿子", "你女儿", "你老公", "你老婆", "你爷爷", "你奶奶", "出事了", "被抓了", "住院了", "出车祸", "进医院", "急需用钱", "快打钱", "别告诉", "别声张", "别让知道"]
        if any(word in content_lower for word in relationship_keywords):
            intents["relationship_fraud"] = True

        # Investment fraud
        investment_keywords = ["投资", "理财", "高回报", "稳赚", "保本", "收益", "日结", "日赚", "月入", "躺赚", "暴富", "内幕", "涨停", "牛股", "带单", "导师", "操盘", "数字货币", "区块链", "挖矿", "合约", "杠杆", "外汇", "期货", "原始股", "股权"]
        if any(word in content_lower for word in investment_keywords):
            intents["investment_fraud"] = True

        # Shopping fraud / fake tasks
        shopping_keywords = ["刷单", "佣金", "点赞", "关注", "兼职", "手工活", "打字员", "录入", "客服", "淘宝刷", "京东刷", "抖音点赞", "关注任务", "任务", "一单", "一任务", "返利", "返现"]
        if any(word in content_lower for word in shopping_keywords):
            intents["shopping_fraud"] = True

        # Job/recruitment fraud
        job_keywords = ["招聘", "工作", "入职", "面试", "押金", "培训费", "体检费", "服装费", "中介费"]
        if any(word in content_lower for word in job_keywords):
            intents["job_fraud"] = True

        # Dating/romance fraud
        dating_keywords = ["裸聊", "约炮", "同城", "附近", "约会", "见面", "保证金", "诚意金", "私密", "激情", "视频", "直播间", "刷礼物", "送礼物"]
        if any(word in content_lower for word in dating_keywords):
            intents["dating_fraud"] = True

        return intents

    def _classify_fraud_type(self, content: str, risk_factors: List[str]) -> str:
        """Fraud type classification"""
        # Relationship fraud (high priority)
        if any(word in content for word in ["我是你爹", "我是你妈", "我是你爸", "我是领导", "我是老板", "你儿子", "你女儿", "你老公", "你老婆"]):
            return "Impersonating Acquaintance Fraud"
        # Impersonating law enforcement
        if any(word in content for word in ["公安", "法院", "检察院", "通缉", "涉案", "警察", "警官", "经侦", "网警", "反诈中心"]):
            return "Impersonating Law Enforcement"
        # Impersonating customer service/platform
        if any(word in content for word in ["客服", "退款", "订单", "快递", "京东", "淘宝", "百万保障", "百万医疗"]):
            return "Impersonating Customer Service"
        # Impersonating bank/institution
        if any(word in content for word in ["银行", "账户", "积分", "额度", "银监", "银保监"]):
            return "Impersonating Bank/Institution"
        # Investment fraud
        if any(word in content for word in ["投资", "理财", "高回报", "稳赚", "数字货币", "区块链", "牛股", "涨停", "内幕"]):
            return "Investment Fraud"
        # Fake task fraud
        if any(word in content for word in ["刷单", "佣金", "点赞", "关注", "兼职", "手工活", "返利", "返现"]):
            return "Fake Task Rebate Fraud"
        # Dating/romance fraud
        if any(word in content for word in ["裸聊", "约炮", "同城", "附近", "刷礼物", "直播间"]):
            return "Dating/Romance Fraud"
        # Prize fraud
        if any(word in content for word in ["中奖", "幸运", "抽奖", "奖品", "奖金"]):
            return "Prize Scam"
        # Direct money demand
        if any(word in content for word in ["转钱", "转我", "给钱", "打钱", "转账", "汇款"]):
            return "Direct Money Demand"
        else:
            return "Other Fraud Types"

    def _get_risk_level(self, score: int) -> str:
        """Determine risk level based on score"""
        if score < 20:
            return "safe"
        elif score < 40:
            return "low"
        elif score < 60:
            return "medium"
        elif score < 80:
            return "high"
        else:
            return "critical"


# Create global instance
content_analyzer = ContentAnalyzer()
