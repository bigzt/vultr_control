import requests
import time
import os
from create_server import get_server_list, VULTR_BASE, vultr_comm_handler, AUTH_HEADER


def destory_server():
    server_list = get_server_list()
    if server_list:
        subid = []
        ip = []
        v6ip = []
        for sid in server_list.keys():
            subid.append(sid)
            ip.append(server_list[sid].get('main_ip'))
            v6ip.append(server_list[sid].get('v6_main_ip'))
            url = VULTR_BASE + 'server/create'
            data = {'SUBID': int(sid)}
            result = vultr_comm_handler(url, 'POST', headers=AUTH_HEADER, data=data)
        print(f"all server destory")
    else:
        print(f'无服务器，不用销毁')


if __name__ == '__main__':
    destory_server()
    os.system('pause')
