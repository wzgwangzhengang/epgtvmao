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
            time.sleep(2 ​**​ attempt + random.uniform(1,3))
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
            time_str_raw = program.contents[0].text.strip()
            match = re.match(r'(\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2}))?', time_str_raw)
            if not match:
                logging.warning(f"无效时间格式：{time_str_raw}")
                continue
            date_part, time_part = match.groups()
            full_time = f"{date_part} {time_part or '00:00'}"
            t_time = datetime.strptime(f"{g_year} {full_time}", '%Y-%m-%d %H:%M')
            
            # 改进标题解析
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
        # 处理首尾时间
        start_of_day = datetime.strptime(f"{g_year} 00:00", '%Y-%m-%d %H:%M').strftime("%Y%m%d%H%M%S")
        end_of_day = datetime.strptime(f"{g_year} 23:59", '%Y-%m-%d %H:%M').strftime("%Y%m%d%H%M%S")
        
        st[0]['startime'] = start_of_day
        last_time = start_of_day
        
        for i in range(len(st)-1):
            current_start = datetime.strptime(st[i]['startime'], '%Y%m%d%H%M%S')
            next_start = datetime.strptime(st[i+1]['startime'], '%Y%m%d%H%M%S')
            duration = (next_start - current_start).total_seconds()
            if duration < 60:
                st[i]['endtime'] = next_start.strftime("%Y%m%d%H%M%S")
            else:
                st[i]['endtime'] = current_start.replace(minute=current_start.minute+30, second=0, microsecond=0).strftime("%Y%m%d%H%M%S")
            last_time = st[i]['endtime']
        st[-1]['endtime'] = end_of_day
        
    return st

def write_tvmao_xml(tv_channel):
    link = "https://www.tvmao.com"
    week = get_week()
    year = get_tomorrow1()
    
    for i, w in enumerate(week):
        for c, u in tv_channel.items():
            sublink, channel_id = u
            programs = get_program_info(link, sublink, w, channel_id, year[i])
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

# ... (保持原有的tvmao_ws_dict, tvmao_ys_dict, tvmao_df_dict不变)
 tvmao_ws_dict = {
    '北京卫视': ['/program/BTV-BTV1-w', 'BTV1'],
    '北京电视台卡酷少儿频道': ['/program/BTV-BTV10-w', 'BTV10'],
    '重庆卫视': ['/program/CCQTV-CCQTV1-w', 'CCQTV1'],
    '东南卫视': ['/program/FJTV-FJTV2-w', 'FJTV2'],
    '厦门电视台厦门卫视': ['/program/XMTV-XMTV5-w', 'XMTV5'],
    '甘肃卫视': ['/program/GSTV-GSTV1-w', 'GSTV1'],
    '广东卫视': ['/program/GDTV-GDTV1-w', 'GDTV1'],
    '深圳卫视': ['/program/SZTV-SZTV1-w', 'SZTV1'],
    '广东南方卫视': ['/program/NANFANG-NANFANG2-w', 'NANFANG2'],
    '广西卫视': ['/program/GUANXI-GUANXI1-w', 'GUANXI1'],
    '贵州卫视': ['/program/GUIZOUTV-GUIZOUTV1-w', 'GUIZOUTV1'],
    '海南卫视': ['/program/TCTC-TCTC1-w', 'TCTC1'],
    '河北卫视': ['/program/HEBEI-HEBEI1-w', 'HEBEI1'],
    '黑龙江卫视': ['/program/HLJTV-HLJTV1-w', 'HLJTV1'],
    '河南卫视': ['/program/HNTV-HNTV1-w', 'HNTV1'],
    '湖北卫视': ['/program/HUBEI-HUBEI1-w', 'HUBEI1'],
    '湖南卫视': ['/program/HUNANTV-HUNANTV1-w', 'HUNANTV1'],
    '湖南电视台金鹰卡通频道': ['/program/HUNANTV-HUNANTV2-w', 'HUNANTV2'],
    '江苏卫视': ['/program/JSTV-JSTV1-w', 'JSTV1'],
    '江西卫视': ['/program/JXTV-JXTV1-w', 'JXTV1'],
    '吉林卫视': ['/program/JILIN-JILIN1-w', 'JILIN1'],
    '辽宁卫视': ['/program/LNTV-LNTV1-w', 'LNTV1'],
    '内蒙古卫视': ['/program/NMGTV-NMGTV1-w', 'NMGTV1'],
    '宁夏卫视': ['/program/NXTV-NXTV2-w', 'NXTV2'],
    '山西卫视': ['/program/SXTV-SXTV1-w', 'SXTV1'],
    '山东卫视': ['/program/SDTV-SDTV1-w', 'SDTV1'],
    '东方卫视': ['/program/DONGFANG-DONGFANG1-w', 'DONGFANG1'],
    '上海广播电视台哈哈炫动卫视': ['/program/TOONMAX-TOONMAX1-w', 'TOONMAX1'],
    '陕西卫视': ['/program/SHXITV-SHXITV1-w', 'SHXITV1'],
    '四川卫视': ['/program/SCTV-SCTV1-w', 'SCTV1'],
    '康巴藏语卫视': ['/program/KAMBA-KAMBA-w', 'KAMBA'],
    '天津卫视': ['/program/TJTV-TJTV1-w', 'TJTV1'],
    '新疆卫视': ['/program/XJTV-XJTV1-w', 'XJTV1'],
    '云南卫视': ['/program/YNTV-YNTV1-w', 'YNTV1'],
    '浙江卫视': ['/program/ZJTV-ZJTV1-w', 'ZJTV1'],
    '青海卫视': ['/program/QHTV-QHTV1-w', 'QHTV1'],
    '西藏电视台藏语卫视': ['/program/XIZANGTV-XIZANGTV1-w', 'XIZANGTV1'],
    '西藏电视台汉语卫视': ['/program/XIZANGTV-XIZANGTV2-w', 'XIZANGTV2'],
    '延边卫视': ['/program/YANBIAN-YANBIAN1-w', 'YANBIAN1'],
    '兵团卫视': ['/program/BINGTUAN-BINGTUAN-w', 'BINGTUAN'],
    '福建海峡卫视': ['/program/HXTV-HXTV-w', 'HXTV'],
    '黄河卫视': ['/program/HHWS-HHWS-w', 'HHWS'],
    '三沙卫视': ['/program/SANSHATV-SANSHATV-w', 'SANSHATV']
}
tvmao_ys_dict = {
    'CCTV-1综合': ['/program/CCTV-CCTV1-w', 'CCTV1'],
    'CCTV-2财经': ['/program/CCTV-CCTV2-w', 'CCTV2'],
    'CCTV-3综艺': ['/program/CCTV-CCTV3-w', 'CCTV3'],
    'CCTV-4国际': ['/program/CCTV-CCTV4-w', 'CCTV4'],
    'CCTV-5体育': ['/program/CCTV-CCTV5-w', 'CCTV5'],
    'CCTV5加': ['/program/CCTV-CCTV5-PLUS-w', 'CCTV5-PLUS'],
    'CCTV-6电影': ['/program/CCTV-CCTV6-w', 'CCTV6'],
    'CCTV-7国防军事': ['/program/CCTV-CCTV7-w', 'CCTV7'],
    'CCTV-8电视剧': ['/program/CCTV-CCTV8-w', 'CCTV8'],
    'CCTV-9纪录': ['/program/CCTV-CCTV9-w', 'CCTV9'],
    'CCTV-10科教': ['/program/CCTV-CCTV10-w', 'CCTV10'],
    'CCTV-11戏曲': ['/program/CCTV-CCTV11-w', 'CCTV11'],
    'CCTV-12法制': ['/program/CCTV-CCTV12-w', 'CCTV12'],
    'CCTV-13新闻': ['/program/CCTV-CCTV13-w', 'CCTV13'],
    'CCTV-14少儿': ['/program/CCTV-CCTV14-w', 'CCTV14'],
    'CCTV-15音乐': ['/program/CCTV-CCTV15-w', 'CCTV15'],
    'CCTV-15奥林匹克': ['/program/CCTV-CCTV16-w', 'CCTV16']
}
tvmao_df_dict = {
    '四川文化旅游频道': ['/program/SCTV-SCTV2-w', 'SCTV2'],
    '四川经济频道': ['/program/SCTV-SCTV3-w', 'SCTV3'],
    '四川新闻频道': ['/program/SCTV-SCTV4-w', 'SCTV4'],
    '四川影视文艺频道': ['/program/SCTV-SCTV5-w', 'SCTV5'],
    '四川星空购物频道': ['/program/SCTV-SCTV6-w', 'SCTV6'],
    '四川妇女儿童频道': ['/program/SCTV-SCTV7-w', 'SCTV7'],
    '峨嵋电影频道': ['/program/SCTV-SCTV8-w', 'SCTV8'],
    '四川公共·乡村': ['/program/SCTV-SCTV9-w', 'SCTV9'],
    '四川科教频道': ['/program/SCTV-SCTV-8-w', 'SCTV-8'],
    '康巴卫视': ['/program/SCTV-KAMBA-TV-w', 'KAMBA-TV'],
    '成都新闻综合频道': ['/program/CHENGDU-CHENGDU1-w', 'CHENGDU1'],
    '成都经济资讯频道': ['/program/CHENGDU-CHENGDU2-w', 'CHENGDU2'],
    '成都都市生活频道': ['/program/CHENGDU-CHENGDU3-w', 'CHENGDU3'],
    '成都影视文艺频道': ['/program/CHENGDU-CHENGDU4-w', 'CHENGDU4'],
    '成都公共频道': ['/program/CHENGDU-CHENGDU5-w', 'CHENGDU5'],
    '成都少儿频道': ['/program/CHENGDU-CDTV-6-w', 'CDTV-6'],
    '成都美食天府': ['/program/CHENGDU-CDTV-7-w', 'CDTV-7'],
    '成都电影频道': ['/program/CHENGDU-CDDYPD-w', 'CDDYPD']
}
if __name__ == "__main__":
    try:
        logging.info("开始生成节目表")
        write_tvmao_xml(tvmao_ys_dict)
        write_tvmao_xml(tvmao_ws_dict)
        write_tvmao_xml(tvmao_df_dict)
        
        # 美化XML输出
        xml_str = ET.tostring(root, encoding='utf-8')
        dom = minidom.parseString(xml_str)
        with codecs.open("tvmao.xml", "w", "utf-8") as f:
            dom.writexml(f, indent="\t", newl="\n", encoding="utf-8")
        
        logging.info("XML文件生成成功")
    except Exception as e:
        logging.critical(f"致命错误：{str(e)}", exc_info=True)
        exit(1)