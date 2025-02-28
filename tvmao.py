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

# 配置日志记录
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def get_year():
    return datetime.now().strftime('%Y')

def get_week():
    wd = datetime.now().strftime('%w')
    return [str(7)] if wd == '0' else [wd, str(int(wd)+1)]

def get_time(times):
    return time.strftime("%Y%m%d%H%M%S", time.localtime(int(times)))

def get_tomorrow():
    today = datetime.today()
    return [today.strftime('%Y%m%d'), (today + timedelta(days=1)).strftime('%Y%m%d')]

def sub_req(a, q, id):
    _keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    str1 = "|" + q
    v = base64.b64encode(str1.encode('utf-8')).decode('utf-8')
    
    str2 = id + "|" + a
    w = base64.b64encode(str2.encode('utf-8')).decode('utf-8')
    
    wday = 7 if datetime.now().strftime('%w') == '0' else int(datetime.now().strftime('%w'))
    F = _keyStr[wday * wday]
    
    return f"{F}{w}{v}"

def is_valid_date(s):
    try:
        if ':' in s:
            time.strptime(s, "%H:%M")
        else:
            return False
        return True
    except:
        return False

def saveXML(root, filename):
    rawText = ET.tostring(root)
    dom = minidom.parseString(rawText)
    with codecs.open(filename, 'w', encoding='utf-8') as f:
        dom.writexml(f, indent='\t', newl='\n', encoding='utf-8')

def parse_time(time_str):
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M",
        "%m-%d %H:%M",
        "%Y%m%d%H%M"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            pass
    return datetime.now()

def get_program_info(link, sublink, week_day, channel_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    }
    url = f"{link}{sublink}{week_day}.html"
    logging.debug(f"Fetching URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch {url}: {e}")
        return []
    
    soup = BeautifulSoup(response.text, 'lxml')
    program_list = soup.find('ul', id="pgrow").find_all('div', class_="over_hide")
    
    programs = []
    current_year = datetime.now().year
    
    for program in program_list:
        title_element = program.find("span", class_="p_show")
        title = title_element.text.strip() if title_element else "未知节目"
        
        time_div = program.contents[0].strip()
        logging.debug(f"Parsing time string: {time_div}")
        
        # 改进的日期时间解析
        date_match = re.search(r'(\d{1,2}-\d{1,2})|(\d{1,2}/\d{1,2})', time_div)
        time_match = re.search(r'(\d{1,2}:\d{2})', time_div)
        
        date_part = None
        if date_match:
            date_candidate = date_match.group(1) or date_match.group(2)
            if not date_candidate:
                continue
            # 统一格式为yyyy-mm-dd
            date_parts = re.sub(r'([/-])', '-', date_candidate).split('-')
            if len(date_parts) != 3:
                continue
            try:
                date_obj = datetime.strptime(f"{current_year}-{date_parts[0]}-{date_parts[1]}", "%Y-%m-%d")
                date_part = date_obj.strftime("%Y-%m-%d")
            except ValueError:
                logging.warning(f"Invalid date format: {date_candidate}")
        
        time_part = time_match.group(1) if time_match else '00:00'
        
        # 处理时间
        try:
            dt = parse_time(f"{date_part or current_year}-01-01 {time_part}")
        except:
            dt = datetime.now()
        
        startime = dt.strftime("%Y%m%d%H%M%S")
        endtime = startime  # 临时设置
        
        programs.append({
            "ch_title": channel_id,
            "startime": startime,
            "title": title,
            "endtime": endtime
        })
    
    # 排序并分配时段
    if not programs:
        return []
    
    # 按开始时间排序
    programs.sort(key=lambda x: x['startime'])
    
    # 生成时间段
    for i in range(len(programs)):
        if i == 0:
            prev_end = datetime.strptime(programs[i]['startime'], "%Y%m%d%H%M%S").replace(second=59)
        else:
            prev_end = datetime.strptime(programs[i-1]['endtime'], "%Y%m%d%H%M%S")
        
        current_start = datetime.strptime(programs[i]['startime'], "%Y%m%d%H%M%S")
        
        if current_start < prev_end:
            new_start = prev_end
            programs[i]['startime'] = new_start.strftime("%Y%m%d%H%M%S")
            programs[i]['endtime'] = new_start.replace(second=59).strftime("%Y%m%d%H%M%S")
        else:
            programs[i]['endtime'] = current_start.replace(second=59).strftime("%Y%m%d%H%M%S")
    
    # 添加默认首播节目
    first_program = programs[0]
    if not first_program['startime'].startswith(get_year()):
        default_start = datetime.now().replace(hour=0, minute=0, second=0).strftime("%Y%m%d%H%M%S")
        programs.insert(0, {
            "ch_title": channel_id,
            "startime": default_start,
            "title": "开台节目",
            "endtime": first_program['startime']
        })
    
    return programs

def write_tvmao_xml(channel_dict, root):
    for channel_name, (sublink, channel_id) in channel_dict.items():
        logging.info(f"Processing channel: {channel_name}")
        week_days = get_week()
        for day in week_days:
            url = f"https://www.tvmao.com{sublink}{day}.html"
            programs = get_program_info(url, sublink, day, channel_id)
            
            # 创建或更新频道节点
            channel_node = None
            for node in root.findall('channel'):
                if node.get('id') == channel_id:
                    channel_node = node
                    break
            if not channel_node:
                channel_node = ET.SubElement(root, 'channel', id=channel_id)
                ET.SubElement(channel_node, 'display-name', lang='zh').text = channel_name
            
            # 添加节目节点
            for prog in programs:
                programme_node = ET.SubElement(channel_node, 'programme',
                                                start=f"{prog['startime']} +0800",
                                                stop=f"{prog['endtime']} +0800",
                                                channel=channel_id)
                title_node = ET.SubElement(programme_node, 'title', lang='zh')
                title_node.text = prog['title']

tvmao_ws_dict = {
    '北京卫视': ['/program_satellite/BTV1-w', 'BTV1'],
    '卡酷少儿频道': ['/program_satellite/BTV10-w', 'BTV10'],
    '重庆卫视': ['/program_satellite/CCQTV1-w', 'CCQTV1'],
    '东南卫视': ['/program_satellite/FJTV2-w', 'FJTV2'],
    '厦门卫视': ['/program_satellite/XMTV5-w', 'XMTV5'],
    '甘肃卫视': ['/program_satellite/GSTV1-w', 'GSTV1'],
    '广东卫视': ['/program_satellite/GDTV1-w', 'GDTV1'],
    '深圳卫视': ['/program_satellite/SZTV1-w', 'SZTV1'],
    '广东南方卫视': ['/program_satellite/NANFANG2-w', 'NANFANG2'],
    '广西卫视': ['/program_satellite/GUANXI1-w', 'GUANXI1'],
    '贵州卫视': ['/program_satellite/GUIZOUTV1-w', 'GUIZOUTV1'],
    '海南卫视': ['/program_satellite/TCTC1-w', 'TCTC1'],
    '河北卫视': ['/program_satellite/HEBEI1-w', 'HEBEI1'],
    '黑龙江卫视': ['/program_satellite/HLJTV1-w', 'HLJTV1'],
    '河南卫视': ['/program_satellite/HNTV1-w', 'HNTV1'],
    '湖北卫视': ['/program_satellite/HUBEI1-w', 'HUBEI1'],
    '湖南卫视': ['/program_satellite/HUNANTV1-w', 'HUNANTV1'],
    '湖南金鹰卡通': ['/program_satellite/HUNANTV2-w', 'HUNANTV2'],
    '江苏卫视': ['/program_satellite/JSTV1-w', 'JSTV1'],
    '江西卫视': ['/program_satellite/JXTV1-w', 'JXTV1'],
    '吉林卫视': ['/program_satellite/JILIN1-w', 'JILIN1'],
    '辽宁卫视': ['/program_satellite/LNTV1-w', 'LNTV1'],
    '内蒙古卫视': ['/program_satellite/NMGTV1-w', 'NMGTV1'],
    '宁夏卫视': ['/program_satellite/NXTV2-w', 'NXTV2'],
    '山西卫视': ['/program_satellite/SXTV1-w', 'SXTV1'],
    '山东卫视': ['/program_satellite/SDTV1-w', 'SDTV1'],
    '东方卫视': ['/program_satellite/DONGFANG1-w', 'DONGFANG1'],
    '哈哈炫动卫视': ['/program_satellite/TOONMAX1-w', 'TOONMAX1'],
    '陕西卫视': ['/program_satellite/SHXITV1-w', 'SHXITV1'],
    '四川卫视': ['/program_satellite/SCTV1-w', 'SCTV1'],
    '康巴卫视': ['/program_satellite/KAMBA-TV-w', 'KAMBA-TV'],
    '天津卫视': ['/program_satellite/TJTV1-w', 'TJTV1'],
    '新疆卫视': ['/program_satellite/XJTV1-w', 'XJTV1'],
    '云南卫视': ['/program_satellite/YNTV1-w', 'YNTV1'],
    '浙江卫视': ['/program_satellite/ZJTV1-w', 'ZJTV1'],
    '青海卫视': ['/program_satellite/QHTV1-w', 'QHTV1'],
    '西藏电视台藏语卫视': ['/program_satellite/XIZANGTV1-w', 'XIZANGTV1'],
    '西藏电视台汉语卫视': ['/program_satellite/XIZANGTV2-w', 'XIZANGTV2'],
    '延边卫视': ['/program_satellite/YANBIAN1-w', 'YANBIAN1'],
    '兵团卫视': ['/program_satellite/BINGTUAN-w', 'BINGTUAN'],
    '福建海峡卫视': ['/program_satellite/HXTV-w', 'HXTV'],
    '黄河卫视': ['/program_satellite/HHWS-w', 'HHWS'],
    '三沙卫视': ['/program_satellite/SANSHATV-w', 'SANSHATV']
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
    '江西移动': ['/program/JXTV-XTV8-w', 'XTV8'],
    '风尚购物': ['/program/JXTV-FSTVGO-w', 'FSTVGO'],
    '江西电视指南': ['/program/JXTV-JXTV-GUIDE-w', 'JXTV-GUIDE'],
    '江西移动': ['/program/JXTV-JXTV8-w', 'JXTV8'],
    '江西陶瓷': ['/program/JXTV-TAOCI-w', 'TAOCI'],
    '江西休闲影视':  ['/program/JXTV-JXXXYS-w', 'JXXXYS']
 }
def main():
    root = ET.Element('tv')
    
    # 分别处理三个频道字典
    write_tvmao_xml(tvmao_ys_dict, root)
    write_tvmao_xml(tvmao_ws_dict, root)
    write_tvmao_xml(tvmao_df_dict, root)
    
    # 保存XML文件
    saveXML(root, "tvmao.xml")
    logging.info("EPG生成完成！")

if __name__ == "__main__":
    main()

