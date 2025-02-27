# -*- coding: utf-8 -*-
import re
import pytz
import sys
import requests
import gzip
from lxml import html
from datetime import datetime, timezone, timedelta

tz = pytz.timezone('Asia/Shanghai')

tz = pytz.timezone('Asia/Shanghai')

cctv_channel = ['cctv1', 'cctv2', 'cctv3', 'cctv4', 'cctv5', 'cctv5plus', 'cctv6','cctv7', 'cctv8', 'cctvjilu', 'cctv10', 'cctv11', 'cctv12','cctv13',
                'cctvchild','cctv15', 'cctv16', 'cctv17', 'cctveurope', 'cctvamerica', 'cctvxiyu', 'cctv4k', 'cctvarabic', 'cctvfrench', 'cctvrussian',
                'shijiedili', 'dianshigouwu', 'taiqiu', 'jingpin', 'shishang', 'hjjc','zhinan', 'diyijuchang', 'fyjc', 'cctvfyzq', 'fyyy',
                'cctvgaowang', 'faxianzhilv','cetv1', 'cetv2', 'cetv3', 'cetv4', 'cctvdoc', 'cctv9', 'btv1', 'btvjishi', 'dongfang', 'hunan', 'shandong', 'zhejiang', 'jiangsu', 'guangdong', 'dongnan', 'anhui', 
               'gansu', 'liaoning', 'travel', 'neimenggu', 'ningxia', 'qinghai', 'xiamen', 'yunnan', 'chongqing', 'jiangxi', 'shan1xi', 
               'shan3xi', 'shenzhen', 'sichuan', 'tianjin', 'guangxi', 'guizhou', 'hebei', 'henan', 'heilongjiang', 'hubei', 'jilin', 
               'yanbian', 'xizang', 'xinjiang', 'bingtuan', 'btvchild', 'sdetv', 'shuhua', 'xianfengjilu', 'shuowenjiezi', 'kuailechuidiao', 'wenwubaoku', 
               'cctvliyuan', 'wushushijie', 'cctvqimo', 'huanqiuqiguan']

def get_epg_data(session, cid, epgdate):
    try:
        api = f"http://api.cntv.cn/epg/epginfo?c={cid}&d={epgdate}"
        response = session.get(api, timeout=10)
        response.raise_for_status()
        print(f"✅ 成功抓取频道 {cid} 数据")
        count_success()
        return response.json()
    except Exception as e:
        print(f"❌ 获取 {cid} 数据失败: {str(e)}", file=sys.stderr)
        return None  # 返回 None 表示失败

def getChannelCNTV(fhandle, channelIDs):
    session = requests.Session()
    epgdate = datetime.now(tz).strftime('%Y%m%d')
    for channel in channelIDs:
        epgdata = get_epg_data(session, channel, epgdate)
        if epgdata is None:
             continue  # 跳过当前频道，继续处理下一个
        if channel in epgdata:
            fhandle.write(f'  <channel id="{channel}">\n')
            fhandle.write(f'    <display-name lang="zh">{epgdata[channel]["channelName"]}</display-name>\n')
            fhandle.write('  </channel>\n')
            count_success()  # 若需要额外统计频道信息写入成功

def getChannelEPG(fhandle, channelIDs):
    session = requests.Session()
    today = datetime.now(tz)
    dates = [today + timedelta(days=i) for i in range(5)]
    
    for channel in channelIDs:
        for date in dates:
            epgdate = date.strftime('%Y%m%d')
            epgdata = get_epg_data(session, channel, epgdate)
            if epgdata is None:
                 continue  # 跳过当前频道，继续处理下一个
            if not epgdata or channel not in epgdata:
                continue
                
            programs = epgdata[channel].get('program', [])
            for detail in programs:
                # 处理毫秒时间戳
                st = detail['st'] // 1000 if detail['st'] > 1e12 else detail['st']
                et = detail['et'] // 1000 if detail['et'] > 1e12 else detail['et']
                
                start = datetime.fromtimestamp(st, tz).strftime('%Y%m%d%H%M%S %z')
                end = datetime.fromtimestamp(et, tz).strftime('%Y%m%d%H%M%S %z')
                
                # 处理跨天节目
                if start > end:
                    print(f"⚠️ 频道 {channel} 的节目跨天：{detail['t']} | 原始时间戳 start={detail['st']} end={detail['et']}")
                    # 自动修正为合法时间（结束时间+1秒）
                    end = (datetime.fromtimestamp(et, tz) + timedelta(seconds=1)).strftime('%Y%m%d%H%M%S %z')
                    print(f"  已自动修正结束时间为：{end}")
                
                fhandle.write(f'  <programme channel="{channel}" start="{start}" stop="{end}">\n')
                fhandle.write(f'    <title lang="zh">{detail["t"]}</title>\n')
                fhandle.write('  </programme>\n')

# 新增统计功能
success_count = 0
def count_success():
    global success_count
    success_count += 1

with gzip.open('cntvepg.xml.gz', 'wt', encoding='utf-8') as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<tv generator-info-name="Fixed EPG" generator-info-url="https://github.com/lxxcp">\n')
    
    # 执行抓取并统计
    for func, channels in [(getChannelCNTV, cctv_channel), (getChannelEPG, cctv_channel)]:
        func(f, channels)
    
    f.write('</tv>')

# 最终检查：若无任何数据则主动报错
if success_count == 0:
    print("⚠️ 未抓取到任何有效数据", file=sys.stderr)
    sys.exit(1)
else:
    print(f"🎉 总计成功写入 {success_count} 个频道数据")
