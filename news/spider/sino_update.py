import django
import os

from celery import shared_task
from django.utils.timezone import make_aware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eco_fin.settings')  # 替换 myproject.settings 为你的实际项目设置路径
django.setup()
from datetime import datetime
from news.models import News

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def get_news_links(base_url, start_path):
    """Traverse through the specified category and collect all news links."""
    all_links = []

    # Initial request to get the first page
    response = requests.get(urljoin(base_url, start_path))
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract news links from the first page
    links = soup.select('.content-text.about.media.media-company ul li a')
    for link in links:
        all_links.append(urljoin(base_url, link.get('href')))

    # Find the total number of pages from the pagination section
    pagination_links = soup.select('.navigation.pagination .nav-links a.page-numbers')
    total_pages = int(pagination_links[-2].text) if pagination_links else 1

    # Traverse through all pages and collect news links
    for page in range(2, total_pages + 1):
        page_url = f"{base_url}{start_path}page/{page}/"
        print(f"Processing page: {page_url}")

        response = requests.get(page_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        links = soup.select('.content-text.about.media.media-company ul li a')
        for link in links:
            all_links.append(urljoin(base_url, link.get('href')))

    print(f"Total links found: {len(all_links)}")
    return all_links


def get_news_content(news_url, news_tag_id):
    """Fetches and parses content from a single news page."""
    try:
        response = requests.get(news_url)
        if response.status_code != 200:
            print(f"Failed to fetch news content from: {news_url}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # 直接定位到新闻详细内容的标题
        title = soup.find('div', class_='content-text about news news-detail').find('div',
                                                                                    class_='title').h4.text.strip()

        # 提取发布日期，注意去除前面的">"
        date_text = soup.find('div', class_='content-text about news news-detail').find('div',
                                                                                        class_='title').h6.text.strip().lstrip(
            '>')
        publish_date = datetime.strptime(date_text, '%Y-%m-%d')
        aware_datetime = make_aware(publish_date)
        # 剩余的部分按原来的逻辑处理
        content_div = soup.find('div', class_='content-text about news news-detail').find('div',
                                                                                    class_='text')
        content_html = str(content_div)

        source = '未知'
        author='未知'
        # print(title,publish_date,content_html)
        return {
            'title': title,
            'date': aware_datetime,
            'author': author,
            'content': content_html,
            'source': source,
            'news_tag_id': news_tag_id  # 添加新闻标签ID到返回的字典中
        }

    except Exception as e:
        print(f"An error occurred while processing the URL {news_url}: {e}")
        return None
@shared_task
def sino_main():
    # 行业新闻：https://www.sino-gf.com.cn/category/media/
    # 绿金新闻：http: // www.greenfinance.org.cn / more.php?cid = 71
    # http: // www.greenfinance.org.cn / more.php?cid = 71 & & page = 2
    base_url = 'https://www.sino-gf.com.cn/category/'
    categories = {
        "时事新闻": ("media/events/", 1),
        "行业资讯": ("media/industry/", 3),
        "案例分析": ("academic/case/", 4),
        "研究报告": ("academic/rreport/", 4),
        "绿研图书馆": ("academic/library/", 4),
        "绿研观点": ("academic/viewpoint/", 4),
        "专题讲座": ("training/lecture/", 6),
        "培训论坛": ("training/forum/", 6),
        "培训课程": ("training/course/", 6),
        "研讨会": ("training/proseminar/", 6),
        "高校平台": ("training/university/", 6),
        "碳金融": ("training/investment/finance/", 3),
        "绿色保险": ("training/university/insurance/", 3),
        "绿色债券": ("training/university/bond/", 3),
        "绿色基金": ("training/university/fund/", 3),
        "绿色投资": ("training/university/invest/", 3),
        "政策研究": ("policies/", 2),
    }
    for category, (path, news_tag_id) in categories.items():
        print(f"正在处理分类：{category}")
        links = get_news_links(base_url, path)
        print(f"在{category}找到{len(links)}个链接")
        for link in links:
            news = get_news_content(link, news_tag_id)  # 传递新闻标签ID
            if news:
                # 使用字典键访问值
                existing_news = News.objects.filter(title=news['title'], author=news['author'],
                                                    publish_date=news['date']).first()

                if existing_news is None:
                    # 如果没有找到相同的新闻，进行保存
                    news_item = News(
                        title=news['title'],
                        content=news['content'],
                        author=news['author'],
                        publish_date=news['date'],
                        source=news['source'],
                        news_tag_id=news['news_tag_id'],  # 确保这与你的 News 模型中的新闻标签ID字段匹配
                    )
                    news_item.save()  # 保存新闻条目
                print(news['title'])  # 举例：打印新闻标题
                # time.sleep(1)


# if __name__ == "__main__":
#     main()
