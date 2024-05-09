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
    links = soup.select('.listnr ul li a')
    for link in links:
        all_links.append(urljoin(base_url, link.get('href')))

    # 确定页码范围
    page_info = soup.select_one('td[id="fanye261394"]').text.strip()
    total_pages = int(page_info.split('/')[1].strip())

    # 遍历剩余页面
    for page in range(total_pages - 1, 0, -1):
        current_page_url = f"{start_path}/{page}.htm"
        full_url = urljoin(base_url, current_page_url)
        print(f"正在处理页面：{full_url}")
        try:
            response = requests.get(full_url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.select('.listnr ul li a')
            for link in links:
                all_links.append(urljoin(base_url, link.get('href')))
        except requests.RequestException as e:
            print(f"请求页面错误: {full_url}, 错误: {e}")

        print(f"总共找到链接数量: {len(all_links)}")
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
        raw_title = soup.select_one('.nry h3').text.strip() if soup.select_one('.nry h3') else '无标题'
        # 分割标题，并保留“|”后的部分（如果存在）
        title = raw_title.split('|')[-1].strip()
        publish_time_info = soup.select_one('.xiab span:nth-of-type(1)').text.strip()
        publish_time = publish_time_info.replace('发布时间：', '').strip()
        naive_publish_time = datetime.strptime(publish_time, '%Y-%m-%d')
        aware_datetime = timezone.make_aware(naive_publish_time, timezone.get_default_timezone())

        news_content_div = soup.find('div', class_='v_news_content')
        for hr_tag in news_content_div.find_all('hr'):
            hr_tag.decompose()
            # 删除特定的<p class="vsbcontent_end">标签，只要它包含“来源”关键字
            # 首先尝试从`.xiab span:nth-of-type(2)`获取作者信息
        author_info_span = soup.select_one('.xiab span:nth-of-type(2)').text.strip() if soup.select_one(
            '.xiab span:nth-of-type(2)') else ''
        author = '未知'  # 默认值
        for div_tag in news_content_div.find_all('div'):
            div_tag.decompose()
        if '作者：' in author_info_span:
            author = author_info_span.replace('作者：', '').strip()
        else:
            # 如果上面没有找到，再检查内容中的最后一个p标签
            author_info_p = news_content_div.find_all('p')[-1].text.strip() if news_content_div.find_all(
                'p') else ''
            if '作者：' in author_info_p:
                author = author_info_p.replace('作者：', '').strip()
            elif '新媒体编辑：' in author_info_p:
                author = author_info_p.replace('新媒体编辑：', '').strip()
        for p_tag in news_content_div.find_all('p', class_='vsbcontent_end'):
            if '来源：' in p_tag.text or '作者：' in p_tag.text or '编辑：' in p_tag.text:
                p_tag.decompose()
        # 转换回字符串，保留标签
        for img in news_content_div.find_all('img'):
            img_src = img.get('src')  # 获取当前的图片src
            if img_src:  # 确保src存在
                full_img_url = urljoin(base_url, img_src)  # 将相对URL转换为完整的URL
                img['src'] = full_img_url  # 更新img标签的src属性
        content = str(news_content_div)
        source_tag = soup.find('p', class_='vsbcontent_end', text=lambda text: text and "来源：" in text)
        source = source_tag.text.replace('来源：', '').strip() if source_tag else '未知'

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
def zy_main():
    base_url = 'https://iigf.cufe.edu.cn'
    categories = {
        "IIGF新闻": ("xwydt/IIGFxw", 6),
        "政策动向": ("xwydt/zcdx", 2),
        "绿金新闻": ("xwydt/ljxw", 1),
        "地方绿金": ("xwydt/dflj", 2),
        "绿金活动": ("xwydt/ljhd", 6)
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
