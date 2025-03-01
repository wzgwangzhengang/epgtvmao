import datetime
import time
import requests
from bs4 import BeautifulSoup as bs
from dateutil import tz
import gzip
import random

# 定义需要抓取的频道
tvmao_ws_dict = {
    '北京卫视': ['/program_satellite/BTV1-w', 'BTV1'],
    '卡酷少儿': ['/program_satellite/BTV10-w', 'BTV10'],
    '重庆卫视': ['/program_satellite/CCQTV1-w', 'CCQTV1'],
    '东南卫视': ['/program_satellite/FJTV2-w', 'FJTV2'],
    '厦门卫视': ['/program_satellite/XMTV5-w', 'XMTV5'],
    '甘肃卫视': ['/program_satellite/GSTV1-w', 'GSTV1'],
    '广东卫视': ['/program_satellite/GDTV1-w', 'GDTV1'],
    '深圳卫视': ['/program_satellite/SZTV1-w', 'SZTV1'],
    '南方卫视': ['/program_satellite/NANFANG2-w', 'NANFANG2'],
    '广西卫视': ['/program_satellite/GUANXI1-w', 'GUANXI1'],
    '贵州卫视': ['/program_satellite/GUIZOUTV1-w', 'GUIZOUTV1'],
    '海南卫视': ['/program_satellite/TCTC1-w', 'TCTC1'],
    '河北卫视': ['/program_satellite/HEBEI1-w', 'HEBEI1'],
    '黑龙江卫视': ['/program_satellite/HLJTV1-w', 'HLJTV1'],
    '河南卫视': ['/program_satellite/HNTV1-w', 'HNTV1'],
    '湖北卫视': ['/program_satellite/HUBEI1-w', 'HUBEI1'],
    '湖南卫视': ['/program_satellite/HUNANTV1-w', 'HUNANTV1'],
    '金鹰卡通': ['/program_satellite/HUNANTV2-w', 'HUNANTV2'],
    '江苏卫视': ['/program_satellite/JSTV1-w', 'JSTV1'],
    '江西卫视': ['/program_satellite/JXTV1-w', 'JXTV1'],
    '吉林卫视': ['/program_satellite/JILIN1-w', 'JILIN1'],
    '辽宁卫视': ['/program_satellite/LNTV1-w', 'LNTV1'],
    '内蒙古卫视': ['/program_satellite/NMGTV1-w', 'NMGTV1'],
    '宁夏卫视': ['/program_satellite/NXTV2-w', 'NXTV2'],
    '山西卫视': ['/program_satellite/SXTV1-w', 'SXTV1'],
    '山东卫视': ['/program_satellite/SDTV1-w', 'SDTV1'],
    '东方卫视': ['/program_satellite/DONGFANG1-w', 'DONGFANG1'],
    '哈哈炫动': ['/program_satellite/TOONMAX1-w', 'TOONMAX1'],
    '陕西卫视': ['/program_satellite/SHXITV1-w', 'SHXITV1'],
    '四川卫视': ['/program_satellite/SCTV1-w', 'SCTV1'],
    '康巴卫视': ['/program_satellite/KAMBA-TV-w', 'KAMBA-TV'],
    '天津卫视': ['/program_satellite/TJTV1-w', 'TJTV1'],
    '新疆卫视': ['/program_satellite/XJTV1-w', 'XJTV1'],
    '云南卫视': ['/program_satellite/YNTV1-w', 'YNTV1'],
    '浙江卫视': ['/program_satellite/ZJTV1-w', 'ZJTV1'],
    '青海卫视': ['/program_satellite/QHTV1-w', 'QHTV1'],
    '西藏卫视藏语': ['/program_satellite/XIZANGTV1-w', 'XIZANGTV1'],
    '西藏卫视': ['/program_satellite/XIZANGTV2-w', 'XIZANGTV2'],
    '延边卫视': ['/program_satellite/YANBIAN1-w', 'YANBIAN1'],
    '兵团卫视': ['/program_satellite/BINGTUAN-w', 'BINGTUAN'],
    '海峡卫视': ['/program_satellite/HXTV-w', 'HXTV'],
    '黄河卫视': ['/program_satellite/HHWS-w', 'HHWS'],
    '三沙卫视': ['/program_satellite/SANSHATV-w', 'SANSHATV']
}

tvmao_ys_dict = {
    'CCTV-1综合': ['/program/CCTV-CCTV1-w', 'CCTV1'],
    'CCTV-2财经': ['/program/CCTV-CCTV2-w', 'CCTV2'],
    'CCTV-3综艺': ['/program/CCTV-CCTV3-w', 'CCTV3'],
    'CCTV-4国际': ['/program/CCTV-CCTV4-w', 'CCTV4'],
    'CCTV-5体育': ['/program/CCTV-CCTV5-w', 'CCTV5'],
    'CCTV-5体育赛事': ['/program/CCTV-CCTV5-PLUS-w', 'CCTV5-PLUS'],
    'CCTV-6电影': ['/program/CCTV-CCTV6-w', 'CCTV6'],
    'CCTV-7国防军事': ['/program/CCTV-CCTV7-w', 'CCTV7'],
    'CCTV-8电视剧': ['/program/CCTV-CCTV8-w', 'CCTV8'],
    'CCTV-9纪录': ['/program/CCTV-CCTV9-w', 'CCTV9'],
    'CCTV-10科教': ['/program/CCTV-CCTV10-w', 'CCTV10'],
    'CCTV-11戏曲': ['/program/CCTV-CCTV11-w', 'CCTV11'],
    'CCTV-12法制': ['/program/CCTV-CCTV12-w', 'CCTV12'],
    'CCTV-13新闻': ['/program/CCTV-CCTV13-w', 'CCTV13'],
    'CCTV-14少儿': ['/program/CCTV-CCTV15-w', 'CCTV15'],
    'CCTV-15音乐': ['/program/CCTV-CCTV16-w', 'CCTV16'],
    'CCTV-16音乐': ['/program/CCTV-CCTVOLY-w', 'CCTVOLY'],
    'CCTV-17音乐': ['/program/CCTV-CCTV17NY-w', 'CCTV17NY'], 
    'CGTN西语': ['/program/CCTV-CCTV17-w', 'CCTV17'],
    'CGTN纪录': ['/program/CCTV-CCTV18-w', 'CCTV18'],
    'CGTN': ['/program/CCTV-CCTV19-w', 'CCTV19'],
    'CCTV-4欧洲': ['/program/CCTV-CCTVEUROPE-w', 'CCTVEUROPE'],
    'CCTV-4美洲': ['/program/CCTV-CCTVAMERICAS-w', 'CCTVAMERICAS'],
    'CGTN法语': ['/program/CCTV-CCTVF-w', 'CCTVF'],
    'CGTN阿语': ['/program/CCTV-CCTVA-w', 'CCTVA'],
    'CGTN俄语': ['/program/CCTV-CCTVR-w', 'CCTVR']
}

tvmao_df_dict = {
    '江西都市': ['/program/JXTV-JXTV2-w', 'JXTV2'],
    '江西经济生活': ['/program/JXTV-JXTV3-w', 'JXTV3'],
    '江西影视旅游': ['/program/JXTV-JXTV4-w', 'JXTV4'],
    '江西公共农业': ['/program/JXTV-JXTV5-w', 'JXTV5'],
    '江西少儿': ['/program/JXTV-JXTV6-w', 'JXTV6'],
    '江西新闻': ['/program/JXTV-JXTV7-w', 'JXTV7'],
    '江西移动': ['/program/JXTV-JXTV8-w', 'JXTV8'],
    '风尚购物': ['/program/JXTV-FSTVGO-w', 'FSTVGO'],
    '江西电视指南': ['/program/JXTV-JXTV-GUIDE-w', 'JXTV-GUIDE'],
    '江西教育': ['/program/JXTV-JXETV-w', 'JXETV'],
    '江西陶瓷': ['/program/JXTV-TAOCI-w', 'TAOCI'],
    '江西休闲影视':  ['/program/JXTV-JXXXYS-w', 'JXXXYS']
}

# 合并所有频道
tvmao_all_channels = {**tvmao_ws_dict, **tvmao_ys_dict, **tvmao_df_dict}

# 设置请求头
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
}

# 获取节目表的核心程序
def get_epg(channel_name, channel_id, dt):
    epgs = []
    msg = ""
    success = 1
    ban = 0  # 标识是否被BAN掉了
    now_date = datetime.datetime.now().date()
    need_date = dt
    delta = need_date - now_date
    now_weekday = now_date.weekday()
    need_weekday = (now_weekday + delta.days) % 7 + 1  # 计算正确的星期数
    url = f"https://lighttv.tvmao.com/qa/qachannelschedule?epgCode={channel_id}&op=getProgramByChnid&epgName=&isNew=on&day={need_weekday}"
    try:
        res = requests.get(url, headers=headers)
        res_j = res.json()
        
        # 检查返回的 JSON 数据结构
        if isinstance(res_j, list) and len(res_j) > 2 and "pro" in res_j[2]:
            datas = res_j[2]["pro"]
            for data in datas:
                title = data["name"]
                starttime_str = data["time"]
                starttime = datetime.datetime.combine(dt, datetime.time(int(starttime_str[:2]), int(starttime_str[-2:])))
                epg = {
                    "channel_id": channel_id,
                    "starttime": starttime,
                    "endtime": None,
                    "title": title,
                    "desc": "",
                    "program_date": dt,
                }
                epgs.append(epg)
        elif isinstance(res_j, list) and len(res_j) == 2 and res_j[0] == 0 and res_j[1] == '':
            # 处理没有节目数据的情况
            success = 0
            msg = f"spider-tvmao-No program data for {channel_name}"
        else:
            success = 0
            msg = f"spider-tvmao-API returned unexpected data structure: {res_j}"
    except Exception as e:
        success = 0
        msg = f"spider-tvmao-{e}"
    ret = {
        "success": success,
        "epgs": epgs,
        "msg": msg,
        "last_program_date": dt,
        "ban": 0,
        "source": "tvmao",
    }
    return ret

# 将 EPG 数据保存为 XML 文件
def save_epg_to_xml(all_epgs):
    xmlhead = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE tv SYSTEM "http://api.torrent-tv.ru/xmltv.dtd"><tv generator-info-name="mxd-epg-xml" generator-info-url="https://epg.mxdyeah.top/">\n'
    xmlbottom = "</tv>"
    tz_sh = tz.gettz("Asia/Shanghai")
    tz_str = " +0800"
    xmldir = "tvmao.xml"

    with open(xmldir, "w", encoding="utf-8") as f:
        f.write(xmlhead)
        # 写入频道信息
        for channel_name, channel_info in tvmao_all_channels.items():
            channel_id = channel_info[1]
            c = f'<channel id="{channel_id}"><display-name lang="zh">{channel_name}</display-name></channel>\n'
            f.write(c)
        # 写入节目信息
        for epg in all_epgs:
            start = epg["starttime"].astimezone(tz=tz_sh).strftime("%Y%m%d%H%M%S") + tz_str
            end = epg["endtime"].astimezone(tz=tz_sh).strftime("%Y%m%d%H%M%S") + tz_str if epg["endtime"] else start
            title = epg["title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;").replace('"', "&quot;")
            desc = epg["desc"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;").replace('"', "&quot;")
            programinfo = f'<programme start="{start}" stop="{end}" channel="{epg["channel_id"]}"><title lang="zh">{title}</title><desc lang="zh">{desc}</desc></programme>\n'
            f.write(programinfo)
        f.write(xmlbottom)

    print(f"已经生成 XML 文件：{xmldir}")

    # 压缩为 gz 文件
    with open(xmldir, 'rb') as f_in:
        with gzip.open('tvmao.xml.gz', 'wb') as f_out:
            f_out.writelines(f_in)
    print("已经生成压缩文件：tvmao.xml.gz")

# 主函数
def main():
    all_epgs = []  # 存储所有频道的节目表
    for i in range(5):  # 抓取当天及后四天的节目单
        dt = datetime.datetime.now().date() + datetime.timedelta(days=i)
        for channel_name, channel_info in tvmao_all_channels.items():
            channel_url_part, channel_id = channel_info
            ret = get_epg(channel_name, channel_id, dt)
            if ret["success"]:
                all_epgs.extend(ret["epgs"])
            else:
                print(f"获取 {channel_name} 的节目表失败: {ret['msg']}")
            time.sleep(random.uniform(1, 3))  # 随机等待1-3秒，避免被封禁
    
    # 将所有节目表保存到一个 XML 文件中
    save_epg_to_xml(all_epgs)

if __name__ == "__main__":
    main()