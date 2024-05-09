import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eco_fin.settings')  # 替换 myproject.settings 为你的实际项目设置路径
django.setup()
from celery import shared_task
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime
from django.utils import timezone
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3 import Retry

from news.models import News, SearchKeyword


@shared_task
def crawl_and_save_news():
    ua = UserAgent()
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    keywords = SearchKeyword.objects.all()
    for keyword_obj in keywords:
        search_word = keyword_obj.keyword
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': ua.random,
            'Referer': 'https://www.thepaper.cn/',
            'Origin': 'https://www.thepaper.cn',
        }

        for page_num in tqdm(range(1, 1001)):
            data = {
                "word": search_word,
                "orderType": 2,
                "pageNum": page_num,
                "pageSize": 10,
                "searchType": 1
            }
            response = session.post('https://api.thepaper.cn/search/web/news', headers=headers, json=data)
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    for item in json_data['data']['list']:
                        news_id = item.get('contId')
                        if news_id:
                            detail_url = f'https://www.thepaper.cn/newsDetail_forward_{news_id}'
                            # print(detail_url)
                            detail_response = session.get(detail_url, headers=headers)
                            if detail_response.status_code == 200:
                                detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
                                title = detail_soup.find('h1').text.strip() if detail_soup.find('h1') else ''
                                content = str(detail_soup.find('div', class_='index_cententWrap__Jv8jK'))
                                # 对新闻来源和作者信息的处理
                                detail_div = detail_soup.find('div', class_='index_left__LfzyH')
                                if detail_div:
                                    divs = detail_div.find_all('div')
                                    source = '来源未知'
                                    author = '作者未知'
                                    if len(divs) > 1:
                                        source_text = divs[1].text.strip()
                                        source = source_text.split('：')[1] if '：' in source_text else '来源未知'
                                    if len(divs) > 0:
                                        author_text = divs[0].text.strip()
                                        author = author_text.split('：')[1] if '作者' in author_text else '作者未知'

                                # 对发布时间的处理
                                publish_time_span = detail_div.find('span') if detail_div else None
                                publish_date = timezone.now()
                                if publish_time_span:
                                    try:
                                        naive_datetime = datetime.strptime(publish_time_span.text.strip(), '%Y-%m-%d %H:%M')
                                        publish_date = timezone.make_aware(naive_datetime, timezone.get_default_timezone())
                                    except ValueError:
                                        pass

                                # 检查并保存新闻
                                existing_news = News.objects.filter(title=title, author=author,
                                                                    publish_date=publish_date).first()
                                if title and not existing_news:
                                    tag_instance = keyword_obj.tag
                                    news_item = News(title=title, content=content, author=author,
                                                     publish_date=publish_date,
                                                     source=source, news_tag=tag_instance)
                                    news_item.save()
                except requests.exceptions.JSONDecodeError:
                    print("解析JSON出错")
            else:
                print(f"请求失败，状态码：{response.status_code}")
def main():
    crawl_and_save_news()
if __name__ == "__main__":
    main()