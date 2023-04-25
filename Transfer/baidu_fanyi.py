import requests
import hashlib
import json


class Transfer:

    def __init__(self):
        # 百度翻译API的URL
        self.url = 'https://fanyi-api.baidu.com/api/trans/vip/translate'

        # 填入你的APP ID和密钥
        self.app_id = '20230424001654499'
        self.secret_key = 'tXa2HtV4Mg3B75rIYgsV'

    def transferTxt(self, text) -> str:
        # 要翻译的文本
        # text = '我想吃个饭，然后回家'

        # 将文本进行MD5加密
        md5 = hashlib.md5()
        md5.update((self.app_id + text + str(123456789) + self.secret_key).encode('utf-8'))
        sign = md5.hexdigest()
        # 构建请求参数
        params = {
            'q': text,
            'from': 'zh',
            'to': 'en',
            'appid': self.app_id,
            'salt': '123456789',
            'sign': sign
        }

        # 发送请求并获取响应
        response = requests.get(self.url, params=params)
        result = json.loads(response.content.decode())
        # 输出翻译结果
        res: str = result['trans_result'][0]['dst']
        print(res)
        return res
