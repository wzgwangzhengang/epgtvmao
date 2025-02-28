# -*- coding: utf-8 -*-
import re
import requests
import time
import codecs
import base64
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from xml.dom import minidom
import logging
import random
from dateutil import parser

# 配置增强版日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)',
    handlers=[
        logging.FileHandler('tvmao.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/118.0'
]

def safe_time_parse(time_str, base_date):
    """
    安全解析时间字符串，支持多种格式：
    1. 完整时间 (YYYY-MM-DD HH:MM)
    2. 仅时间 (HH:MM)
    3. 时间段 (HH:MM-HH:MM)
    4. 特殊标记 (直播/重播)
    """
    try:
        # 清理空白字符
        time_str = re.sub(r'\s+', ' ', time_str.strip())
        
        # 处理特殊标记
        if time_str in {'直播', '重播', 'LIVE'}:
            return base_date.replace(hour=12, minute=0)  # 默认中午12点

        # 提取第一个时间部分
        time_part = re.split(r'[-\s]', time_str)[0]
        
        # 包含日期的情况
        if re.match(r'\d{4}-\d{2}-\d{2}', time_part):
            dt = parser.parse(time_part, fuzzy=True)
            return dt.replace(year=base_date.year)
            
        # 仅时间的情况
        if re.match(r'\d{1,2}:\d{2}', time_part):
            time_obj = datetime.strptime(time_part, "%H:%M")
            return base_date.replace(hour=time_obj.hour, minute=time_obj.minute)
            
        # 最后尝试dateutil解析
        return parser.parse(time_str, fuzzy=True, default=base_date)
        
    except Exception as e:
        logging.warning(f"时间解析失败: {time_str} | 错误: {str(e)}")
        return base_date  # 返回基准日期作为保底值

def get_program_info(link, sublink, week_day, id_name, g_year):
    """获取频道节目信息（增强版）"""
    st = []
    base_date = datetime.strptime(g_year, "%Y-%m-%d")
    
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': link,
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
    
    website = f"{link}{sublink}{week_day}.html"
    logging.info(f"开始处理: {id_name} - {website}")

    # 带指数退避的重试机制
    for attempt in range(3):
        try:
            response = requests.get(website, headers=headers, timeout=(10, 30))
            response.raise_for_status()
            break
        except Exception as e:
            if attempt == 2:
                logging.error(f"请求失败: {website} | 错误: {str(e)}")
                return []
            delay = (2 ** attempt) + random.uniform(1, 3)
            time.sleep(delay)
    else:
        return []

    soup = BeautifulSoup(response.text, 'lxml')
    
    # 改进的选择器，兼容页面结构变化
    container = soup.find('ul', id='pgrow') or soup.find('div', class_='program-list')
    if not container:
        logging.warning(f"找不到节目列表容器: {id_name}")
        return []
    
    program_items = container.find_all(['div.over_hide', 'li.program-item'], recursive=True)
    
    for item in program_items:
        try:
            # 时间部分解析
            time_element = item.find(class_=re.compile(r'time|start'))
            raw_time = time_element.text.strip() if time_element else ''
            
            # 标题解析
            title_element = item.find(class_=re.compile(r'p_show|title|name'))
            title = title_element.text.strip() if title_element else '未知节目'
            
            # 安全解析时间
            program_time = safe_time_parse(raw_time, base_date)
            startime = program_time.strftime("%Y%m%d%H%M%S")
            
            st.append({
                "ch_title": id_name,
                "startime": startime,
                "title": title,
                "endtime": "000000"
            })
            
        except Exception as e:
            logging.error(f"条目解析失败: {item} | 错误: {str(e)}")
            continue

    # 时间区间填充逻辑
    if st:
        # 按时间排序
        st.sort(key=lambda x: x['startime'])
        
        # 填充结束时间
        for i in range(len(st)-1):
            st[i]['endtime'] = st[i+1]['startime']
        
        # 处理最后一条
        last_end = base_date.replace(hour=23, minute=59)
        st[-1]['endtime'] = last_end.strftime("%Y%m%d%H%M%S")
        
        # 添加第一条的起始时间
        first_start = base_date.replace(hour=0, minute=0)
        if st[0]['startime'] != first_start.strftime("%Y%m%d%H%M%S"):
            st.insert(0, {
                "ch_title": id_name,
                "startime": first_start.strftime("%Y%m%d%H%M%S"),
                "title": "节目开始",
                "endtime": st[0]['startime']
            })
            
    return st

def generate_xml(channels):
    """生成XML文件（改进版）"""
    root = ET.Element('tv', {
        "generator-info-name": "TVMAO EPG Generator",
        "generator-info-url": "https://github.com/your-repo",
        "source-info-name": "电视猫",
        "source-info-url": "https://www.tvmao.com"
    })
    
    for chan_name, chan_data in channels.items():
        programs = get_program_info(
            link="https://www.tvmao.com",
            sublink=chan_data[0],
            week_day=datetime.now().weekday() + 1,
            id_name=chan_data[1],
            g_year=datetime.now().strftime("%Y-%m-%d")
        )
        
        if not programs:
            continue
            
        # 创建频道节点
        chan_node = ET.SubElement(root, 'channel', id=chan_data[1])
        ET.SubElement(chan_node, 'display-name').text = chan_name
        
        # 添加节目单
        for prog in programs:
            programme = ET.SubElement(root, 'programme',
                start=f"{prog['startime']} +0800",
                stop=f"{prog['endtime']} +0800",
                channel=chan_data[1]
            )
            ET.SubElement(programme, 'title').text = prog['title']
            
    return root

def main():
    """主执行函数"""
    try:
        # 频道配置（示例）
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
        
        # 生成XML结构
        xml_root = generate_xml({**tvmao_ys_dict, **tvmao_ws_dict, **tvmao_df_dict})
        
        # 美化输出
        xml_str = ET.tostring(xml_root, encoding='utf-8')
        dom = minidom.parseString(xml_str)
        
        with codecs.open("tvmao.xml", "w", "utf-8") as f:
            dom.writexml(f, indent="  ", newl="\n", encoding="utf-8")
            
        logging.info("XML文件生成成功")
        
    except Exception as e:
        logging.critical(f"致命错误: {str(e)}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main()





