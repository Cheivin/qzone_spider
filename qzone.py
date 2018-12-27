# -*- coding: utf-8 -*-

import json
import time
import csv
from enum import Enum

import requests
import threadpool
from selenium import webdriver


# 计算空间gtk
def get_g_tk():
    p_skey = cookie_dict['p_skey']
    h = 5381
    for i in p_skey:
        h += (h << 5) + ord(i)
        g_tk = h & 2147483647
    return g_tk


qq_number = '*********'
password = '*********'
login_url = 'https://i.qq.com/'

driver = webdriver.Chrome()
driver.get(login_url)
# 进入登陆的ifame
driver.switch_to_frame('login_frame')
driver.find_element_by_xpath('//*[@id="switcher_plogin"]').click()
time.sleep(1)
# 填写QQ
driver.find_element_by_xpath('//*[@id="u"]').send_keys(qq_number)
# 填写密码
driver.find_element_by_xpath('//*[@id="p"]').send_keys(password)
time.sleep(1)
# 登录
driver.find_element_by_xpath('//*[@id="login_button"]').click()
time.sleep(1)

# 获取cookies
cookie_list = driver.get_cookies()
cookie_dict = {}
for cookie in cookie_list:
    if 'name' in cookie and 'value' in cookie:
        cookie_dict[cookie['name']] = cookie['value']

headers = {
    "Origin": "https://user.qzone.qq.com"
    , "Referer": "https://user.qzone.qq.com/{}/infocenter?_t_=0.9872252117622393".format(qq_number)
    ,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36"
}
g_tk = get_g_tk()


# 获取好友列表
def get_friend_list():
    res = requests.get(
        "https://h5.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/tfriend/friend_show_qqfriends.cgi?uin={}&follow_flag=0&groupface_flag=0&fupdate=1&g_tk={}"
            .format(qq_number, g_tk)
        , headers=headers
        , cookies=cookie_dict)
    res_data = json.loads(res.text[len('_Callback('):-len(');')])
    friend_list = {}
    for friend in res_data['data']['items']:
        if friend['uin'] != qq_number:
            friend_list[friend['uin']] = friend['remark'] if len(friend['remark']) > 1 else friend['uin']
    return friend_list


# 获取添加好友时间
def get_friend_addtime(friend):
    res = requests.get(
        "https://user.qzone.qq.com/proxy/domain/r.qzone.qq.com/cgi-bin/friendship/cgi_friendship?activeuin={}&situation=1&isCalendar=1&g_tk={}&passiveuin={}"
            .format(qq_number, g_tk, friend)
        , headers=headers
        , cookies=cookie_dict)
    res_data = json.loads(res.text[len('_Callback('):-len(');')])
    # return res_data['data']['addFriendTime']
    return time.strftime("%Y-%m-%d", time.localtime(res_data['data']['addFriendTime']))


# return time.strftime("%Y-%m-%d", res_data['data']['addFriendTime'])

# 星座定义
class Constellation(Enum):
    未知 = -1
    白羊座 = 0
    金牛座 = 1
    双子座 = 2
    巨蟹座 = 3
    狮子座 = 4
    处女座 = 5
    天秤座 = 6
    天蝎座 = 7
    射手座 = 8
    摩羯座 = 9
    水瓶座 = 10
    双鱼座 = 11


class Sex(Enum):
    未知 = 0
    男 = 1
    女 = 2


# 获取好友信息
def get_friend_info(friend):
    res = requests.get(
        "https://h5.qzone.qq.com/proxy/domain/base.qzone.qq.com/cgi-bin/user/cgi_userinfo_get_all?uin={}&fupdate=1&rd=0.9787380697834234&g_tk={}"
            .format(friend, g_tk)
        , headers=headers
        , cookies=cookie_dict)
    res_data = json.loads(res.text[len('_Callback('):-len(');')])['data']
    info = {
        # 'sex': res_data['sex']
        # , 'constellation': res_data['constellation']
        'sex': Sex(res_data['sex']).name
        , 'constellation': Constellation(res_data['constellation']).name
        , 'age': res_data['age']
        , 'birthyear': res_data['birthyear']
        , 'birthday': res_data['birthday']
        , 'country': res_data['country']
        , 'province': res_data['province']
        , 'city': res_data['city']
    }
    return info


info_list = []
error_list = []


def get_friend(friend):
    try:
        info = get_friend_info(friend)
        info['addTime'] = get_friend_addtime(friend)
        info['qq'] = friend
        # return info
        info_list.append(info)
    except:
        error_list.append(friend)


print("获取好友列表...")
friend_list = get_friend_list()
print("获取好友信息...")
# 设置线程池容量，创建线程池
pool_size = 10
pool = threadpool.ThreadPool(pool_size)
# 创建工作请求
reqs = threadpool.makeRequests(get_friend, friend_list.keys())
# 将工作请求放入队列
[pool.putRequest(req) for req in reqs]
pool.wait()
print("抓取完成...\n")
# with open('data.txt', 'w') as json_file:
#    json.dump(info_list, json_file, ensure_ascii=False)  # 加上ensure_ascii=False，使中文正常显示

with open('friend.csv', 'w', encoding='utf-8-sig') as csv_file:
    csv_out = csv.DictWriter(csv_file,
                             ['qq', 'sex', 'constellation', 'age', 'birthyear', 'birthday', 'country', 'province',
                              'city', 'addTime'])
    csv_out.writeheader()
    csv_out.writerows(info_list)

print(error_list)
