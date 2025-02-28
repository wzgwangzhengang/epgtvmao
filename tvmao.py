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
saveXML(root,"tvmao.xml")# -*- coding: utf-8 -*-
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

# 星期映射表（中文转数字）
WEEKDAY_MAP = {
    "星期一": "1", "星期二": "2", "星期三": "3",
    "星期四": "4", "星期五": "5", "星期六": "6", "星期日": "7"
}

def get_program_info(link, sublink, week_day, id_name, g_year):
    st = []
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': link,
        'X-Requested-With': 'XMLHttpRequest'
    }
    website = f"{link}{sublink}{week_day}.html"  # 使用数字星期
    
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
            # 改进时间解析逻辑
            time_str_raw = program.contents[0].text.strip() if program.contents else ""
            if not time_str_raw:
                continue
            
            # 使用更灵活的正则表达式
            match = re.match(r'^(\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2}))?', time_str_raw)
            if not match:
                logging.warning(f"无效时间格式：{time_str_raw}")
                continue
            date_part, time_part = match.groups()
            full_time = f"{date_part} {time_part if time_part else '00:00'}"
            
            # 处理日期时间
            # 修改前的代码
# t_time=datetime.strptime(g_year+" "+program.contents[0].text,'%Y-%m-%d %H:%M')

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
    # 动态获取当前星期并转换为数字
    target_date = datetime.now()
    target_weekday = target_date.strftime("%A")
    # 转换中文星期名称（根据系统语言设置可能需要调整）
    cn_weekday = target_date.strftime("%w")  # 0-6对应周日到周六
    week_num = str((int(cn_weekday) + 1) % 7 or 7)  # 转换为1-7
    
    year = [datetime.now().strftime('%Y')]
    
    for c, u in tv_channel.items():
        sublink, channel_id = u
        programs = get_program_info(link, sublink, week_num, c, year[0])
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

# 修正后的频道配置
tv_channels = {
    '北京卫视': ['/program/BTV1-w', 'BTV1'],        # 正确路径示例：/program/BTV1-w5.html
    'CCTV-1综合': ['/program/CCTV1-w', 'CCTV1'],  # 正确路径示例：/program/CCTV1-w5.html
    '湖南卫视': ['/program/HNTV-w', 'HNTV'],       # 正确路径示例：/program/HNTV-w5.html
    '东方卫视': ['/program/DFWS-w', 'DFTV'],       # 正确路径示例：/program/DFWS-w5.html
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