import requests
import time
import os

APIKEY = '你的vultr API KEY'

AUTH_HEADER = {'API-KEY': APIKEY}
VULTR_BASE = 'https://api.vultr.com/v1/'
SNAPSHOTID = '你的快照ID'
SV_DCID = '1'  # 12 硅谷 4 西雅图 39 迈阿密 默认顺序为 硅谷 西雅图 迈阿密，修改顺序在59行，其他地方ID请自行查找
VPSPLANID = '201'  # 5 usd/m 的VPS，带价格检查，提价不会建立服务器
SS_PATH = '你的ss目录路径'  # 到exe那一级
IP_TYPE = 'ipv6'  # ipv6/v4 设置，ipv4 改为 'ipv4'

# SS 配置，建议直接从配置文件copy内容到128~178行，保留130行的 {ip} 
SS_PORT = '你的SS端口'
SS_PASSWORD = '你的SS密码'
SS_ENCRYPT = '你的SS加密方式'  # 字符串全拼 e.g xchacha20-ietf-poly1305

def vultr_comm_handler(url, method, headers=None, data=None, params=None):
    if method == 'GET':
        result = requests.get(url, headers=headers, params=params)
    elif method == 'POST':
        result = requests.post(url, headers=headers, data=data, params=params)
        if result.status_code != 200:
            print(result.text)
    else:
        raise TypeError('method must be GET or POST')
    try:
        result.json()
    except:
        return result.text
    return result.json()


def get_server_list():
    url = VULTR_BASE + 'server/list'
    result = vultr_comm_handler(url, 'GET', headers=AUTH_HEADER)
    return result


def get_regions_list():
    url = VULTR_BASE + 'regions/list'
    result = vultr_comm_handler(url, 'GET')
    return result


def get_plans_list():
    url = VULTR_BASE + 'plans/list'
    result = vultr_comm_handler(url, 'GET')
    return result


def check_plans():
    global SV_DCID
    result = get_plans_list()
    if result[VPSPLANID]['price_per_month'] != '5.00' or result[VPSPLANID]['bandwidth_gb'] != '1024':
        raise ValueError('vultr TMD 换plan了')
    SV_DCID_LIST = [12, 4, 39]  # 12 硅谷 4 西雅图 39 迈阿密
    for svdcid in SV_DCID_LIST:
        if svdcid in result[VPSPLANID]['available_locations']:
            SV_DCID = str(svdcid)
            break
    else:
        raise ValueError('3个候选机房都TMD不可用')


def check_region():
    global SV_DCID
    result = get_regions_list()
    if result[SV_DCID]['name'] != 'Silicon Valley':
        raise ValueError('vultr修改了机房DCID！')
    return True


def gen_new_server():
    server_list = get_server_list()
    if server_list:
        subid = []
        ip = []
        v6ip = []
        for sid in server_list.keys():
            subid.append(sid)
            ip.append(server_list[sid].get('main_ip'))
            v6ip.append(server_list[sid].get('v6_main_ip'))
        print(f"already have servers, SUBID: {subid}, IP: {ip} V6IP: {v6ip}")
        if IP_TYPE == 'ipv6'：
            create_SS_config_file(v6ip[0])
        else:
            create_SS_config_file(ip[0])
    else:
        check_region()
        check_plans()
        url = VULTR_BASE + 'server/create'
        data = {'DCID': int(SV_DCID), 'VPSPLANID': int(VPSPLANID), 'OSID': 164, 'SNAPSHOTID': SNAPSHOTID,
                'enable_ipv6': 'yes'}
        result = vultr_comm_handler(url, 'POST', headers=AUTH_HEADER, data=data)
        try:
            newsid = result['SUBID']
            print(f'服务器创建成功，SUBID{result} 等待启动成功获得IP')
            time.sleep(2)
            while True:
                server_list = get_server_list()
                if server_list[newsid]['server_state'] != 'ok':
                    time.sleep(8)
                else:
                    break
            ipv4 = server_list[newsid].get('main_ip')
            ipv6 = server_list[newsid].get('v6_main_ip')
            print(f"new server create, SUBID: {newsid}, IP: {ipv4} V6IP: {ipv6}")
            if IP_TYPE == 'ipv6'：
                create_SS_config_file(ipv6)
            else:
                create_SS_config_file(ipv4)
        except Exception:
            print(f'服务器创建失败，vultr返回值{result}')


def create_SS_config_file(ip):
    print(f'正在改写SS配置')
    config_file = SS_PATH + '/gui-config.json'
    text = f"""{{
  "configs": [
    {{
      "server": "{ip}",
      "server_port": "{SS_PORT}",
      "password": "{SS_PASSWORD}",
      "method": "{SS_ENCRYPT}",
      "plugin": "",
      "plugin_opts": "",
      "plugin_args": "",
      "remarks": "",
      "timeout": 5
    }},
  ],
  "strategy": null,
  "index": 0,
  "global": false,
  "enabled": false,
  "shareOverLan": true,
  "isDefault": false,
  "localPort": 1080,
  "pacUrl": null,
  "useOnlinePac": false,
  "secureLocalPac": false,
  "availabilityStatistics": false,
  "autoCheckUpdate": true,
  "checkPreRelease": true,
  "isVerboseLogging": true,
  "logViewer": {{
    "topMost": false,
    "wrapText": false,
    "toolbarShown": false,
    "Font": "Consolas, 8pt",
    "BackgroundColor": "Black",
    "TextColor": "White"
  }},
  "proxy": {{
    "useProxy": false,
    "proxyType": 0,
    "proxyServer": "",
    "proxyPort": 0,
    "proxyTimeout": 3
  }},
  "hotkey": {{
    "SwitchSystemProxy": "",
    "SwitchSystemProxyMode": "",
    "SwitchAllowLan": "",
    "ShowLogs": "",
    "ServerMoveUp": "",
    "ServerMoveDown": ""
  }}
}}
"""
    with open(config_file, 'w', encoding='utf8') as f:
        f.write(text)
    print('正在启动SS client')
    os.startfile(f"{SS_PATH}/Shadowsocks.exe")

if __name__ == '__main__':
    gen_new_server()
    os.system('pause')

