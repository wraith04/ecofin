import django
import os

from celery import shared_task

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eco_fin.settings')  # 替换 myproject.settings 为你的实际项目设置路径
django.setup()

from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timezone
from news.models import News
from django.utils import timezone

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}


def get_news_links(base_url, start_path):
    """遍历指定分类下的所有页面，收集所有新闻链接"""
    all_links = []

    # 首页不含页码，特别处理
    current_path = f"{start_path}.htm"
    response = requests.get(urljoin(base_url, current_path), headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    # 从首页提取新闻链接
    links = soup.select('.listCont li a')
    for link in links:
        all_links.append(urljoin(base_url, link.get('href')))

    # 确定页码范围
    # Find the total number of pages
    pagination = soup.find('ul', class_='pagination')
    if pagination:
        total_pages = len(pagination.find_all('a'))  # Counting the number of <a> elements

        # Loop through each page
        for page in range(2, total_pages + 1):
            current_page_url = f"{start_path}?page={page}"
            full_url = urljoin(base_url, current_page_url)
            print(f"正在处理页面：{full_url}")
            try:
                response = requests.get(full_url, headers=headers)
                soup = BeautifulSoup(response.content, 'html.parser')
                links = soup.select('.listCont li a')
                for link in links:
                    all_links.append(urljoin(base_url, link.get('href')))
            except requests.RequestException as e:
                print(f"请求页面错误: {full_url}, 错误: {e}")

            print(f"总共找到链接数量: {len(all_links)}")
    else:
        print("未找到pagination元素")

    return all_links

def get_news_content(news_url, news_tag_id, base_url):
    """获取单个新闻页面的内容，并接受新闻标签ID作为参数"""
    try:
        response = requests.get(news_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch news content: {news_url}")
            return None
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 从原始标题中删除“|”前的内容
        title_tag = soup.find('div', class_='tit').find_all('h1')[0]
        raw_title = title_tag.text.strip() if title_tag else '无标题'
        title = raw_title.split(' ')[1].strip() if ' ' in raw_title else raw_title.strip()

        publish_time_tag = soup.find('div', class_='tit').find_all('p')[0]

        publish_time = publish_time_tag.text.strip() if publish_time_tag else None
        # print(publish_time)
        naive_publish_time = datetime.strptime(publish_time, '%Y-%m-%d') if publish_time else None
        aware_datetime = timezone.make_aware(naive_publish_time,
                                             timezone.get_default_timezone()) if naive_publish_time else None

        # Extract news content
        # Extract news content
        news_content_div = soup.find('div', class_='news')
        content = None
        if news_content_div:
            # Find all <img> tags within the news content div
            video_div = soup.find('div', id="video")
            if video_div:
                video_div.decompose()
            script_tags = soup.find_all('script')
            for script in script_tags:
                if 'myvideo' in script.text or 'origin' in script.text:
                    script.decompose()
            img_tags = news_content_div.find_all('img')
            # Add base_url to src attribute of each <img> tag
            for img_tag in img_tags:
                img_src = img_tag.get('src')
                if img_src:
                    img_tag['src'] = urljoin(base_url, img_src)
            # Convert the news_content_div to string
            content = str(news_content_div)

        # Extract author and source
        author_tag = soup.find('b', style="font-family:宋体,SimSun;")
        author_info = author_tag.text.strip() if author_tag else None
        if author_info:
            # 分割字符串提取作者
            author = author_info.split('：')[1].split('\xa0')[0].strip() if '：' in author_info else '未知'
            # 如果作者是"本站"，则改为"中国清洁发展机制基金"
            if author == "本站":
                author = "中国清洁发展机制基金"
        else:
            author = "未知"
        source = author_info.split('来源：')[1].strip() if author_info and '来源：' in author_info else '未知'

        # 在返回的字典中包含新闻标签ID
        return {
            'title': title,
            'publish_time': aware_datetime,
            'author': author,
            'source': source,
            'content': content,
            'news_tag_id': news_tag_id  # 添加新闻标签ID
        }
    except Exception as e:
        print(f"An error occurred while processing {news_url}: {e}")
        return None

@shared_task
def zg_main():
    base_url = 'https://www.cdmfund.org'
    categories = {
        "图片新闻": ("photo.html", 1),
        "基金动态": ("jjdt.html", 3),
        "国内新闻": ("gnxw.html", 1),
        "国际新闻": ("world.html", 1),
        "碳市场动态": ("tscdt.html", 3),
        "绿色金融": ("lsjr.html", 2),
        "COP26": ("COP26.html", 6)
    }

    for category, (path, news_tag_id) in categories.items():
        print(f"正在处理分类：{category}")
        links = get_news_links(base_url, path)
        print(f"在{category}找到{len(links)}个链接")
        for link in links:
            news = get_news_content(link, news_tag_id, base_url)  # 传递新闻标签ID
            if news:
                # 使用字典键访问值
                existing_news = News.objects.filter(title=news['title'], author=news['author'],
                                                    publish_date=news['publish_time']).first()

                if existing_news is None:
                    # 如果没有找到相同的新闻，进行保存
                    news_item = News(
                        title=news['title'],
                        content=news['content'],
                        author=news['author'],
                        publish_date=news['publish_time'],
                        source=news['source'],
                        news_tag_id=news['news_tag_id'],  # 确保这与你的 News 模型中的新闻标签ID字段匹配
                    )
                    news_item.save()  # 保存新闻条目
                print(news['title'])  # 举例：打印新闻标题
                time.sleep(1)

