import requests
import os
import re

with open(os.path.join(os.path.dirname(__file__), 'cookie.txt')) as f:
    cookie = f.read()

f = requests.get(
    'https://www.maersk.com.cn/tracking/MRSU3638119',
    headers={
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.55',
        'cookie': cookie
    }
)

print(f.text)
