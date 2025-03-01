import datetime
import time
import requests
from bs4 import BeautifulSoup as bs
from dateutil import tz
import gzip
import random
import json

# 读取配置文件
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 获取所有频道信息
tvmao_all_channels = config["channels"]

# 设置请求头
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
}

# 获取节目表的核心程序
def get_epg(channel_name, channel_id, dt, retries=3):
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
    
    for attempt in range(retries):
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
                break  # 成功获取数据，退出重试循环
            elif isinstance(res_j, list) and len(res_j) == 2 and res_j[0] == 0 and res_j[1] == '':
                # 处理没有节目数据的情况
                success = 0
                msg = f"spider-tvmao-No program data for {channel_name}"
                break  # 没有数据，退出重试循环
            else:
                success = 0
                msg = f"spider-tvmao-API returned unexpected data structure: {res_j}"
                if attempt < retries - 1:
                    time.sleep(random.uniform(1, 2))  # 等待2-5秒后重试
        except Exception as e:
            success = 0
            msg = f"spider-tvmao-{e}"
            if attempt < retries - 1:
                time.sleep(random.uniform(1, 2))  # 等待2-5秒后重试
    
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
    now_date = datetime.datetime.now().date()  # 当前日期
    now_weekday = now_date.weekday()  # 当前星期几（0=周一，6=周日）

    for i in range(5):  # 抓取当天及后四天的节目单
        dt = now_date + datetime.timedelta(days=i)  # 计算目标日期
        delta_days = (dt - now_date).days  # 计算与当前日期的差值
        need_weekday = (now_weekday + delta_days) % 7 + 1  # 计算正确的星期数（W1-W7，跨周后 W8-W14）

        # 如果跨越到下一周，星期数需要增加7
        if delta_days >= (7 - now_weekday):
            need_weekday += 7

        print(f"正在抓取日期: {dt}，星期数: W{need_weekday}")

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