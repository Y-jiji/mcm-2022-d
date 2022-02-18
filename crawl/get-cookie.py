import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar

URL_ROOT = 'https://www.maersk.com.cn/'
values = {'name': '******', 'password': '******'}
postdata = urllib.parse.urlencode(values).encode()
user_agent = r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
headers = {'User-Agent': user_agent}

cookie_filename = 'cookie.txt'
cookie = http.cookiejar.LWPCookieJar(cookie_filename)
handler = urllib.request.HTTPCookieProcessor(cookie)
opener = urllib.request.build_opener(handler)

request = urllib.request.Request(URL_ROOT, postdata, headers)
try:
    response = opener.open(request)
except urllib.error.URLError as e:
    print(e.reason)

cookie.save(ignore_discard=True, ignore_expires=True)  # 保存cookie到cookie.txt中
for item in cookie:
    print('Name = ' + item.name)
    print('Value = ' + item.value)
