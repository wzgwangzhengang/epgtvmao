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


def get_year():
    now = datetime.now()
    year = now.strftime('%Y')
    return str(year)

def get_week():
    now = datetime.now()
    week = now.strftime('%w')
    wd = int(week)
    if wd == 0:
        w = [str(7)]
    else:
        w = [str(wd), str(wd + 1)]
    return w


def get_time(times):
    time_r = time.strftime("%Y%m%d%H%M%S", time.localtime(int(times)))
    return time_r


def get_tomorrow1():
    day = []
    day.append(datetime.today().strftime('%Y-%m-%d'))
    now = datetime.today()
    delta = now + timedelta(days=1)
    date2 = delta.strftime('%Y-%m-%d')
    day.append(date2)
    return day


def get_tomorrow():
    day = []
    day.append(datetime.today().strftime('%Y%m%d'))
    now = datetime.today()
    delta = now + timedelta(days=1)
    date2 = delta.strftime('%Y%m%d')
    day.append(date2)
    return day


def sub_req(a, q, id):
    _keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="

    str1 = "|" + q
    v = base64.b64encode(str1.encode('utf-8'))

    str2 = id + "|" + a
    w = base64.b64encode(str2.encode('utf-8'))

    str3 = time.strftime("%w")
    wday = (7 if (int(str3) == 0) else int(str3))
    F = _keyStr[wday * wday]

    return (F + str(w, 'utf-8') + str(v, 'utf-8'))


def is_valid_date(strdate):
    try:
        if ":" in strdate:
            time.strptime(strdate, "%H:%M")
        else:
            return False
        return True
    except:
        return False


def saveXML(root, filename, indent="\t", newl="\n", encoding="utf-8"):
    rawText = ET.tostring(root)
    dom = minidom.parseString(rawText)
    with codecs.open(filename, 'w', 'utf-8') as f:
        dom.writexml(f, "", indent, newl, encoding)


def get_program_info(link, sublink, week_day, id_name):
    st = []
    headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    }
    website = f"{link}{sublink}{week_day}.html"
    r = requests.get(website, headers=headers)
    soup = BeautifulSoup(r.text, 'lxml')

    list_program_div = soup.find('ul', id="pgrow").find_all('div', class_="over_hide")

    current_year = datetime.now().year

    for program in list_program_div:
        temp_title = program.find("span", class_="p_show")
        title = temp_title.text.strip() if temp_title else "未知节目"

        time_div = program.contents[0].text.strip()
        date_match = re.search(r'(\d{1,2}-\d{1,2})', time_div)
        time_match = re.search(r'(\d{1,2}:\d{2})', time_div)
        
        date_part = date_match.group(1) if date_match else '01-01'
        time_part = time_match.group(1) if time_match else '00:00'

        try:
            t_time = datetime.strptime(f"{current_year}-{date_part} {time_part}", '%Y-%m-%d %H:%M')
        except ValueError:
            try:
                t_time = datetime.strptime(f"{current_year + 1}-{date_part} {time_part}", '%Y-%m-%d %H:%M')
            except:
                t_time = datetime(current_year, 1, 1, 0, 0)

        startime = t_time.strftime("%Y%m%d%H%M%S")
        pro_dic = {"ch_title": id_name, "startime": startime, "title": title, "endtime": "000000"}
        st.append(pro_dic)

    if st:
        first_pro = st[0]
        if not first_pro['startime'].startswith(str(current_year)):
            t1 = datetime(current_year, 1, 1, 0, 0).strftime("%Y%m%d%H%M%S")
            st.insert(0, {"ch_title": id_name, "startime": t1, "title": "未知节目", "endtime": first_pro['startime']})

    for i in range(len(st) - 1):
        st[i]['endtime'] = st[i + 1]['startime']

    if st:
        last_pro = st[-1]
        end_time = datetime.strptime(last_pro['startime'], "%Y%m%d%H%M%S").replace(hour=23, minute=59, second=59)
        st[-1]['endtime'] = end_time.strftime("%Y%m%d%H%M%S")

    return st


def write_tvmao_xml(tv_channel):
    link = "https://www.tvmao.com"
    week = get_week()
    for w in week:
        for c, u in tv_channel.items():
            sublink = u[0]
            channel_id = u[1]
            try:
                programs = get_program_info(link, sublink, w, channel_id)
            except Exception as e:
                print(f"获取{c}节目表失败: {str(e)}")
                continue

            # 创建或更新频道节点
            channel_node = None
            for node in root.findall('channel'):
                if node.get('id') == channel_id:
                    channel_node = node
                    break
            if not channel_node:
                channel_node = ET.SubElement(root, 'channel', id=channel_id)
                ET.SubElement(channel_node, 'display-name', lang='zh').text = c

            # 添加节目单
            for prog in programs:
                programme = ET.SubElement(root, 'programme',
                                          start=f"{prog['startime']} +0800",
                                          stop=f"{prog['endtime']} +0800",
                                          channel=channel_id)
                ET.SubElement(programme, 'title', lang='zh').text = prog['title']

            print(f"已处理频道: {c}")

tvmao_ws_dict = {
    '北京卫视': ['/program/BTV1-w', 'BTV1'],
    '卡酷少儿频道': ['/program/BTV10-w', 'BTV10'],
    '重庆卫视': ['/program/CCQTV1-w', 'CCQTV1'],
    '东南卫视': ['/program/FJTV2-w', 'FJTV2'],
    '厦门电视台厦门卫视': ['/program/XMTV5-w', 'XMTV5'],
    '甘肃卫视': ['/program/GSTV1-w', 'GSTV1'],
    '广东卫视': ['/program/GDTV1-w', 'GDTV1'],
    '深圳卫视': ['/program/SZTV1-w', 'SZTV1'],
    '广东南方卫视': ['/program/NANFANG2-w', 'NANFANG2'],
    '广西卫视': ['/program/GUANXI1-w', 'GUANXI1'],
    '贵州卫视': ['/program/GUIZOUTV1-w', 'GUIZOUTV1'],
    '海南卫视': ['/program/TCTC1-w', 'TCTC1'],
    '河北卫视': ['/program/HEBEI1-w', 'HEBEI1'],
    '黑龙江卫视': ['/program/HLJTV1-w', 'HLJTV1'],
    '河南卫视': ['/program/HNTV1-w', 'HNTV1'],
    '湖北卫视': ['/program/HUBEI1-w', 'HUBEI1'],
    '湖南卫视': ['/program/HUNANTV1-w', 'HUNANTV1'],
    '湖南电视台金鹰卡通频道': ['/program/HUNANTV2-w', 'HUNANTV2'],
    '江苏卫视': ['/program/STV1-w', 'JSTV1'],
    '江西卫视': ['/program/JXTV1-w', 'JXTV1'],
    '吉林卫视': ['/program/JILIN1-w', 'JILIN1'],
    '辽宁卫视': ['/program/LNTV1-w', 'LNTV1'],
    '内蒙古卫视': ['/program/NMGTV1-w', 'NMGTV1'],
    '宁夏卫视': ['/program/NXTV2-w', 'NXTV2'],
    '山西卫视': ['/program/SXTV1-w', 'SXTV1'],
    '山东卫视': ['/program/SDTV1-w', 'SDTV1'],
    '东方卫视': ['/program/DONGFANG1-w', 'DONGFANG1'],
    '哈哈炫动卫视': ['/programTOONMAX1-w', 'TOONMAX1'],
    '陕西卫视': ['/programSHXITV1-w', 'SHXITV1'],
    '四川卫视': ['/programSCTV1-w', 'SCTV1'],
    '康巴藏语卫视': ['/programKAMBA-w', 'KAMBA'],
    '天津卫视': ['/programTJTV1-w', 'TJTV1'],
    '新疆卫视': ['/programXJTV1-w', 'XJTV1'],
    '云南卫视': ['/programYNTV1-w', 'YNTV1'],
    '浙江卫视': ['/programZJTV1-w', 'ZJTV1'],
    '青海卫视': ['/programQHTV1-w', 'QHTV1'],
    '西藏电视台藏语卫视': ['/programXIZANGTV1-w', 'XIZANGTV1'],
    '西藏电视台汉语卫视': ['/programXIZANGTV2-w', 'XIZANGTV2'],
    '延边卫视': ['/programYANBIAN1-w', 'YANBIAN1'],
    '兵团卫视': ['/programBINGTUAN-w', 'BINGTUAN'],
    '福建海峡卫视': ['/programHXTV-w', 'HXTV'],
    '黄河卫视': ['/programHHWS-w', 'HHWS'],
    '三沙卫视': ['/program_favorite/SANSHATV-SANSHATV-w', 'SANSHATV']
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
  }
root = ET.Element('tv', generator-info-name="Generated by 3mile", generator-info-url="https://3mile.top")

print("开始生成节目数据...")
write_tvmao_xml(tvmao_ys_dict)
write_tvmao_xml(tvmao_ws_dict)
write_tvmao_xml(tvmao_df_dict)

print("保存XML文件...")
saveXML(root, "tvmao.xml")
print("EPG生成完成！")