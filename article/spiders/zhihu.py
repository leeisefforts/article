import re
import time
import hmac
from hashlib import sha1
import json
import base64
import requests
import PIL.Image as Image
import scrapy
import os
from zheye.zheye import zheye

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

try:
    import cookielib
except:
    import http.cookiejar as cookielib


class ZhihuSpider(scrapy.Spider):
    name = "zhihu"

    session = requests.session()

    session.cookies = cookielib.LWPCookieJar(filename="cookies.txt")  # cookie存储文件，

    try:
        session.cookies.load(ignore_discard=True)  # 从文件中读取cookie
    except:
        print("cookie 未能加载")

    agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"

    header = {
        "origin": "https://www.zhihu.com",
        "Referer": "https://www.zhihu.com/signup?next=%2F",
        "User-Agent": agent,
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Host': 'www.zhihu.com',
        'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4,zh-TW;q=0.2',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'keep-alive'

    }

    def start_requests(self):
        text = self.is_login()

    # 不使用scrapy进行第一步登录
    def parse(self, response):
        pass

    def get_xsrf(self):

        responses = self.session.post("https://www.zhihu.com/signin", headers=self.header)

        # print(response.cookies['_xsrf'])
        return responses.cookies['_xsrf']

    def get_signature(self,time_str):

        h = hmac.new(key='d1b964811afb40118a12068ff74a12f4'.encode('utf-8'), digestmod=sha1)

        grant_type = 'password'
        client_id = 'c3cef7c66a1843f8b3a9e6a1e3160e20'
        source = 'com.zhihu.web'
        now = time_str
        h.update((grant_type + client_id + source + now).encode('utf-8'))
        return h.hexdigest()

    def get_captcha(self):

        '''
        :authority: www.zhihu.com
        :method: GET
        :path: /api/v3/oauth/captcha?lang=cn
        :scheme: https
        accept: application/json, text/plain, */*
        accept-encoding: gzip, deflate, br
        accept-language: zh-CN,zh;q=0.9,en;q=0.8
        authorization: oauth c3cef7c66a1843f8b3a9e6a1e3160e20
        cookie: d_c0="AIDk5lsxrA2PTn6UE7w8ZXwIcLwr6s4V8TM=|1527673963"; q_c1=29e9198d965c42b4b4d13820bc7023db|1527673963000|1527673963000; _zap=a0bc8c13-50e7-484b-abde-db97010a065b; l_cap_id="YzIxYmFmNzg0YjViNGZmODljNTIwMjUwMTQ5NWY0NTY=|1527688563|f3bfccc25e61ab0e6c92295650f257e2f9cd779b"; r_cap_id="YTE3M2JlMWQ4NWQzNDA2NzllYThmMWYxNjMxZmRhMTY=|1527688563|be9b0cd7843bf090e5e0194ceb29a99fc60a1cce"; cap_id="ZWFjYTg3ODljMzI0NDVmOTgyYmE0NjRiMGQyZGRmYmU=|1527688563|4636e8decd51156afe879407f16e6c7f57e222ce"; tgw_l7_route=5bcc9ffea0388b69e77c21c0b42555fe; _xsrf=405b7e07-d4f5-4b35-8b70-3e129d97a4d8; capsion_ticket="2|1:0|10:1527727674|14:capsion_ticket|44:Y2M3YTcwYWQ3OGFiNGIxMjk3MWUwY2I5ZWQ0OWM0ZjQ=|ed0700eadd8466ffd6f4c61dfbce11a1f4d11483f32f1ae8262501a7fd859558"
        if-none-match: "fa4cf03c0ac47ca1c52ed2df2b71dfda86db6655"
        referer: https://www.zhihu.com/signup?next=%2F
        user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36
        x-udid: AIDk5lsxrA2PTn6UE7w8ZXwIcLwr6s4V8TM=
        '''

        self.header.update({
            "authorization": "oauth c3cef7c66a1843f8b3a9e6a1e3160e20"
        })
        captcha_url = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=cn'
        response = self.session.get(captcha_url, headers=self.header)
        captcha = {}
        captcha['img_size'] = [200, 44]

        r = re.findall('"show_captcha":(\w+)', response.text)
        if r[0] == 'false':
            return ''
        else:
            response = self.session.put('https://www.zhihu.com/api/v3/oauth/captcha?lang=cn', headers=self.header)
            show_captcha = json.loads(response.text)['img_base64']

            with open('captcha.gif', 'wb') as f:
                f.write(base64.b64decode(show_captcha))
            try:
                z = zheye()
                positions = z.Recognize(os.path.abspath('captcha.gif'))
                pos_arr = []

                if len(positions) == 2:
                    if positions[0][1] > positions[1][1]:
                        pos_arr.append([float(format(positions[1][1], '0.2f')), float(format(positions[1][0], '0.2f'))])
                        pos_arr.append([float(format(positions[0][1], '0.2f')), float(format(positions[0][0], '0.2f'))])
                    else:
                        pos_arr.append([float(format(positions[0][1], '0.2f')), float(format(positions[0][0], '0.2f'))])
                        pos_arr.append([float(format(positions[1][1], '0.2f')), float(format(positions[1][0], '0.2f'))])
                else:
                    pos_arr.append([float(format(positions[0][1], '0.2f')), float(format(positions[0][0], '0.2f'))])

                captcha['input_points'] = pos_arr

            except:
                print("解析图片失败！")

            return captcha

    def zhihu_login(self, account, password):

        # 知乎登录
        time_str = str(int(time.time()))
        xsrf = self.get_xsrf()
        self.header.update({
            "X-Xsrftoken": xsrf
        })
        post_url = "https://www.zhihu.com/api/v3/oauth/sign_in"
        post_data = {
            "client_id": "c3cef7c66a1843f8b3a9e6a1e3160e20",
            "content-type": "application/x-www-form-urlencoded",
            "grant_type": "password",
            "captcha": str(self.get_captcha()),
            "timestamp": time_str,
            "source": "com.zhihu.web",
            "signature": self.get_signature(time_str),
            "username": account,
            "password": password,
            "lang": "cn",
            "ref_source": "other_",
            "utm_source": "baidu",
            "captcha_type": "cn"
        }
        #responses = scrapy.Request(post_url, method="POST", headers=self.header, body=post_data, cookies=self.session.cookies)
        responses = self.session.post(post_url, data=post_data, headers=self.header, cookies=self.session.cookies)
        if responses.status_code == 201:
            # 保存cookie，下次直接读取保存的cookie，不用再次登录

            responses = self.session.post("https://www.zhihu.com", headers=self.header, cookies=self.session.cookies)
            print(responses.text)
            self.session.cookies.save()
            return responses.text
        else:
            return 'fail'


    def is_login(self):
        # 通过个人中心页面返回状态码来判断是否登录
        # 通过allow_redirects 设置为不获取重定向后的页面
        self.zhihu_login("leeisefforts@163.com", "leekobe24")
