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
    # for i in range(wd,8):
    #    w.append(str(i))
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
    # print(wday);
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
        #writer = codecs.lookup('utf-8')[3](f)
        dom.writexml(f, "", indent, newl, encoding)


def get_program_info(link, sublink, week_day, id_name, g_year):
    st = []
    # year=get_tomorrow1()
    # week=get_week()
    # now_date=year[week.index(str(week_day))]
    headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache'
    }
    # website = '%s%s%s' % (link, sublink,week_day)
    website = link + sublink + str(week_day) + ".html"
    r = requests.get(website, headers=headers)

    soup = BeautifulSoup(r.text, 'lxml')  # 使用BeautifulSoup解析这段代码
    # 获取节目列表
    list_program_div = soup.find(name='ul', attrs={
        "id": "pgrow"
    }).find_all(name='div', attrs={"class": "over_hide"})
    # list_program_div = soup.find(attrs={"id": "pgrow"}).find_all("li")

    for program in list_program_div:
        # con_num = len(program.contents)
        # title = program.contents[con_num - 1].text

        temp_title=program.find_all("span", attrs={"class": "p_show"})
        title=temp_title[0].text
        
        # t_time = '%s %s' % (g_year, program.contents[0].text)
        # 修改后的代码
        # 获取并清理节目时间文本
        program_time_text = program.contents[0].text.strip()

        # 分割日期和时间部分（假设格式为"MM-DD HH:mm"或只有"MM-DD"）
        time_parts = program_time_text.split()
        date_part = time_parts[0] if time_parts else ""
        time_part = time_parts[1] if len(time_parts) > 1 else "00:00"  # 默认时间

        # 组合完整日期时间字符串
        try:
          full_date_str = f"{g_year}-{date_part}"  # 假设g_year为年份（如2025）
          full_time_str = f"{full_date_str} {time_part}"
    
        # 解析时间
          t_time = datetime.strptime(full_time_str, '%Y-%m-%d %H:%M')
        except ValueError as e:
           print(f"解析时间失败：{full_time_str}，错误：{e}")
        # 可设置默认时间或跳过该条目
        t_time = datetime.strptime(f"{g_year}-{date_part} 00:00", '%Y-%m-%d %H:%M')
        startime=t_time.strftime("%Y%m%d%H%M%S")
        pro_dic={"ch_title":id_name,"startime":startime,"title":title,"endtime":"000000"}
        st.append(pro_dic)
        # print(startime + "    " + title)
        # print("----------------")
    
    test_data=st[0]
    t_id=test_data["ch_title"]
    t_st=test_data["startime"]
    t_ti=test_data["title"]

    test_startime=re.sub('^\d{8}','',t_st)
    if test_startime!="000000":
        t1=datetime.strptime(g_year+" 00:00",'%Y-%m-%d %H:%M')
        t2=t1.strftime("%Y%m%d%H%M%S")
        pro_dic={"ch_title":id_name,"startime":t2,"title":"未知节目","endtime":t_st}
        st.insert(0,pro_dic)
    
    for i,v in enumerate(st):
        if i < len(st)-2:
            endtime=st[i+1]
            v["endtime"]=endtime["startime"]
            st[i]=v
        else:
            tt=datetime.strptime(g_year+" 23:59",'%Y-%m-%d %H:%M')
            endtime=tt.strftime("%Y%m%d%H%M%S")
            v["endtime"]=endtime
            st[i]=v
    return st


def write_tvmao_xml(tv_channel):
    link = "https://www.tvmao.com"
    week = get_week()
    year = get_tomorrow1()
    for i, w in enumerate(week):
        for c, u in tv_channel.items():
            sublink = u[0]
            # t=get_tianmao_programme(u[1],u[0])

            t = get_program_info(link, sublink, w, u[1], year[i])

            index = len(root.findall('channel'))
            child = ET.Element('channel')
            root.insert(index, child)

            child.set("id", u[1])
            child_name = ET.SubElement(child, "display-name")
            child_name.set("lang", "zh")
            child_name.text = c

            for lop in t:
                channel_id=lop['ch_title']
                title=lop['title']
                startime=lop['startime']
                endtime=lop['endtime']

                programme_sub=ET.SubElement(root,"programme")
                programme_sub.set("start",startime+" +0800")
                programme_sub.set("stop",endtime+" +0800")
                programme_sub.set("channel",channel_id)

                programme_title=ET.SubElement(programme_sub,"title")
                programme_title.set("lang","zh")
                programme_title.text=title
            print("已经获取"+c)
        # ET.dump(root)

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

root = ET.Element('tv')
root.set("generator-info-name", "Generated by 3mile")
root.set("generator-info-url", "https://3mile.top")

write_tvmao_xml(tvmao_ys_dict)
write_tvmao_xml(tvmao_ws_dict)
write_tvmao_xml(tvmao_df_dict)
saveXML(root,"tvmao.xml")