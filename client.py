# -*- coding: utf-8 -*-
import os
import re
import uuid
import shutil
import requests
from pathlib import Path
from urllib import request as ure
from flask import request, jsonify, Flask
from flask_apscheduler import APScheduler


# 获取更新url和更新版本号的url
get_version_url = 'http://192.168.10.123/erp/aiBox/selectVersion'

allfile = []
md5_list = []
ignore_list = ['.idea']
updateList = {}
directory = os.getcwd()
version = ''
download_url = ''
version_time = 0


class Config(object):
    # 任务列表
    JOBS = [
        {
            'id': 'job1',
            'func': '__main__:file_name',  # 方法名
            # 'args': (version, ),  # 入参
            'trigger': 'interval',  # interval表示循环任务
            'seconds': 10,  # 每隔version_time执行一次
        }
    ]


# 获取本地mac地址
def get_mac_address():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    mac_addr = ":".join([mac[e:e + 2] for e in range(0, 11, 2)])
    return mac_addr


# 向服务器定时请求，获取更新地址和版本号
def get_version(url, mac_addr):
    global download_url, version, version_time
    payload = {'mac': mac_addr}
    r = requests.post(url, data=payload)
    res = r.json()
    code = res['code']
    if code == 10000:
        data = res['data']
        data = data[0]
        download_url = data['url']
        version = data['version']
        version_time = data['versionTime']
    else:
        print('获取版本号异常')
        # return None
    # return download_url, version, version_time


def file_name():
    file_dir = directory
    file_list = os.listdir(file_dir)
    for file in file_list:
        if file in ignore_list:
            continue
        file_path = Path(file_dir + '/' + file)
        if file_path.is_file():
            continue
        else:
            if find_v(file) is True:
                current_version = file
                if current_version != version:
                    # 删除原version目录
                    print('正在删除旧版本%s' % current_version)
                    clear_up(current_version)
                    # 下载新version
                    print('请下载最新版本%s' % version)
                    download_file(download_url)
                    break
                else:
                    print('当前版本不需要更新')
                    break
            else:
                # 当前路径有目录但非v目录
                print('请下载最新版本%s' % version)
                download_file(download_url)
                break


def find_v(file_name):
    recom = re.compile(r'^[v]+\d*\d$')
    res_list = recom.findall(file_name)
    print(res_list)
    if res_list:
        print('存在版本')
        return True
    else:
        print('不存在版本')
        return False


def download_file(url):
    new_dir = directory + '/' + version
    os.makedirs(new_dir)
    file_name = url.split('/')[-1]
    file_path = new_dir + '/' + file_name
    ure.urlretrieve(url, file_path)
    print('新版本下载成功')


def clear_up(file_dir):
    del_dir = directory + '/' + file_dir
    shutil.rmtree(del_dir)
    print('删除成功')


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config.from_object(Config())


# 首页
@app.route("/", methods=['GET'])
def hello():
    if request.method == "GET":
        return "Hello,Python Server!I'm Python Client!"


# 获取当前版本
@app.route("/checkVersion", methods=['GET'])
def check():
    if request.method == "GET":
        code, current_version, msg = get_current_verson(directory)
        return_data = {
            'Code': code,
            'Version': current_version,
            'Msg': msg,
        }
        return jsonify(return_data)


def get_current_verson(file_dir):
    file_list = os.listdir(file_dir)
    for file in file_list:
        if file.startswith('v'):
            file_path = Path(file_dir + '/' + file)
            if file_path.is_dir():
                current_version = file
                msg = '版本正常'
                return 1000, current_version, msg
            else:
                msg = '请客户端及时下载'
                return 2000, '', msg
        else:
            msg = '请客户端及时下载'
            return 3000, '', msg


if __name__ == "__main__":
    mac = get_mac_address()
    get_version(get_version_url, mac)
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    app.run(host='0.0.0.0', port=1314, debug=True)
