# -*- coding: utf-8 -*-
import re
import requests
import json
import time
import codecs
import base64
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from xml.dom import minidom
import logging
import random

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('tvmao.log'), logging.StreamHandler()]
)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/118.0',
    'Mozilla/5.0 (iPad; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/605.1.15 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/605.1.15'
]

def get_program_info(link, sublink, week_day, id_name, g_year):
    st = []
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': link,
        'X-Requested-With': 'XMLHttpRequest'
    }
    website = f"{link}{sublink}{week_day}.html"
    
    # 带重试的请求机制
    for attempt in range(3):
        try:
            response = requests.get(website, headers=headers, timeout=15)
            response.raise_for_status()
            break
        except Exception as e:
            if attempt == 2:
                logging.error(f"请求失败：{website}，错误：{str(e)}")
                return []
            time.sleep(2 ** attempt + random.uniform(1,3))
    else:
        return []

    soup = BeautifulSoup(response.text, 'lxml')
    
    # 增强的页面元素查找
    pgrow_ul = soup.find('ul', {'id': 'pgrow'})
    if not pgrow_ul:
        logging.warning(f"未找到节目列表容器：{id_name} - {website}")
        return []
    
    program_divs = pgrow_ul.find_all('div', class_='over_hide')
    if not program_divs:
        logging.warning(f"未找到节目条目：{id_name} - {website}")
        return []

    # 处理节目数据
    for program in program_divs:
        try:
            # 改进时间解析
            time_str_raw = program.contents[0].text.strip() if program.contents else ""
            if not time_str_raw:
                continue
            
            match = re.match(r'^(\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2}))?$', time_str_raw)
            if not match:
                logging.warning(f"无效时间格式：{time_str_raw}")
                continue
            date_part, time_part = match.groups()
            full_time = f"{date_part} {time_part or '00:00'}"
            
            # 打印调试信息
            logging.debug(f"Parsed time: {full_time} -> {g_year}{full_time}")
            
            t_time = datetime.strptime(f"{g_year} {full_time}", '%Y-%m-%d %H:%M')
            
            # 标题解析
            title_elements = program.select(['.p_show', '.show-info', 'h3', '.title'])
            title = title_elements[0].text.strip() if title_elements else "未知节目"
            
            startime = t_time.strftime("%Y%m%d%H%M%S")
            st.append({
                "ch_title": id_name,
                "startime": startime,
                "title": title,
                "endtime": "000000"
            })
        except Exception as e:
            logging.error(f"解析错误：{str(e)} - {website}")
            continue

    # 填充时间段
    if st:
        # 首尾时间强制覆盖全天
        start_of_day = datetime.strptime(f"{g_year} 00:00", '%Y-%m-%d %H:%M').strftime("%Y%m%d%H%M%S")
        end_of_day = datetime.strptime(f"{g_year} 23:59", '%Y-%m-%d %H:%M').strftime("%Y%m%d%H%M%S")
        
        st[0]['startime'] = start_of_day
        for i in range(len(st)-1):
            current_start = datetime.strptime(st[i]['startime'], '%Y%m%d%H%M%S')
            next_start = datetime.strptime(st[i+1]['startime'], '%Y%m%d%H%M%S')
            duration = (next_start - current_start).total_seconds()
            
            if duration < 60:
                st[i]['endtime'] = next_start.strftime("%Y%m%d%H%M%S")
            else:
                # 处理跨天或长间隔
                st[i]['endtime'] = current_start.replace(minute=59, second=59).strftime("%Y%m%d%H%M%S")
        st[-1]['endtime'] = end_of_day
        
    return st

def write_tvmao_xml(tv_channel):
    link = "https://www.tvmao.com"
    week = ['星期五']  # 根据实际需求修改
    year = [datetime.now().strftime('%Y')]  # 使用当前年份
    
    for c, u in tv_channel.items():
        sublink, channel_id = u
        programs = get_program_info(link, sublink, week[0], c, year[0])
        if not programs:
            continue

        # 创建XML节点
        channel_node = ET.SubElement(root, 'channel', id=channel_id)
        ET.SubElement(channel_node, 'display-name', lang='zh').text = c
        
        for prog in programs:
            programme = ET.SubElement(root, 'programme',
                start=f"{prog['startime']} +0800",
                stop=f"{prog['endtime']} +0800",
                channel=channel_id
            )
            ET.SubElement(programme, 'title', lang='zh').text = prog['title']
        
        logging.info(f"成功处理频道：{c} ({channel_id})")

# XML根节点
root = ET.Element('tv', {
    "generator-info-name": "Generated by Enhanced Script",
    "generator-info-url": "https://github.com/yourrepo",
    "source-info-name": "TVMAO",
    "source-info-url": "https://www.tvmao.com",
    "xmlns": "http://www.guideplus.org/schema/epg"
})

# 频道配置（根据需要修改）
tv_channels = {
    '北京卫视': ['/program/BTV-BTV1-w', 'BTV1'],
    'CCTV-1综合': ['/program/CCTV-CCTV1-w', 'CCTV1'],
    '湖南卫视': ['/program/HNTV-HNTV-w', 'HNTV'],
    '东方卫视': ['/program/DONGFANGTV-DONGFANGTV-w', 'DFTV'],
    # 添加更多频道
}

if __name__ == "__main__":
    try:
        logging.info("开始生成节目表")
        write_tvmao_xml(tv_channels)
        
        # 美化XML输出
        xml_str = ET.tostring(root, encoding='utf-8')
        dom = minidom.parseString(xml_str)
        with codecs.open("tvmao.xml", "w", "utf-8") as f:
            dom.writexml(f, indent="\t", newl="\n", encoding="utf-8")
        
        logging.info("XML文件生成成功")
    except Exception as e:
        logging.critical(f"致命错误：{str(e)}", exc_info=True)
        exit(1)
