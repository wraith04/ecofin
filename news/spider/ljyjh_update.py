import django
import os

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

    # 首页处理
    response = requests.get(urljoin(base_url, start_path), headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    # 提取首页的新闻链接
    links = soup.select('.rightulli ul li a')
    for link in links:
        all_links.append(urljoin(base_url, link.get('href')))

    # 提取总页数
    # 假设“共有 76 条记录 共 6 页”这样的文本位于某个元素中
    # 假设原来的代码是这样的
    page_info_text = soup.select_one('.listtail').text.strip()

    # 改进后的代码
    try:
        page_info_text = soup.select_one('.listtail').text.strip()
        # 确保文本格式符合预期
        if '共' in page_info_text and '页' in page_info_text:
            total_pages = int(page_info_text.split('共')[1].split('页')[0].strip())
        else:
            print("未能从页面提取到总页数信息，检查是否有更改页面结构。")
            total_pages = 50  # 或者设定为默认值，比如1
    except Exception as e:
        print(f"提取总页数时出错: {e}")
        total_pages = 50  # 或者设定为默认值，比如1

    # 遍历除首页外的其它页
    for page in range(2, total_pages + 1):  # 假设页码从2开始
        current_page_url = f"{start_path}&&page={page}"
        full_url = urljoin(base_url, current_page_url)
        print(f"正在处理页面：{full_url}")

        try:
            response = requests.get(full_url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.select('.rightulli ul li a')
            for link in links:
                all_links.append(urljoin(base_url, link.get('href')))
        except requests.RequestException as e:
            print(f"请求页面错误: {full_url}, 错误: {e}")

    print(f"总共找到链接数量: {len(all_links)}")
    return all_links


def get_news_content(news_url, news_tag_id, base_url):
    """获取单个新闻页面的内容，并接受新闻标签ID作为参数"""
    # http: // www.greenfinance.org.cn / more.php?cid = 71 & & page = 2
    try:
        response = requests.get(news_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch news content: {news_url}")
            return None
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find('div', class_='titleh').h1.text.strip()
        # 从<h2>标签提取发布时间、来源和作者信息
        h2_text = soup.select_one('.titleh h2').text.strip()
        # 假设格式总是日期 + 来源 + 作者
        parts = h2_text.split('　')  # 使用中文空格分割
        publish_time = datetime.strptime(parts[0], '%Y-%m-%d')
        aware_datetime = timezone.make_aware(publish_time, timezone.get_default_timezone())
        source = parts[1].replace('来源：', '').strip() if len(parts) > 1 else "未知"
        author = parts[2].replace('作者:', '').strip() if len(parts) > 2 else "未知"


        content_div = soup.select_one('.titleh')
        if content_div:
            # 移除不需要的`<script>`和`<style>`标签，以及`<h1>`和`<h2>`标签
            for unnecessary_tag in content_div.find_all(['script', 'style', 'h1', 'h2']):
                unnecessary_tag.decompose()

            # 无需删除来源信息的<span>标签，直接保留
            for span_tag in content_div.find_all('span', class_='se'):
                span_tag.decompose()
            # 调整图片链接
            for img in content_div.find_all('img'):
                img_src = img.get('src')
                if img_src:
                    full_img_url = urljoin(base_url, img_src)  # 确保base_url已定义且正确湖州创设零碳建筑贷 助推首个近零碳建筑项目落地
                    img['src'] = full_img_url

            # 将修改后的content_div转换为HTML字符串
            content_html = str(content_div)
        else:
            content_html = ""
            print("未找到内容div，无法提取新闻内容。")

        # print(content_html)
        return {
            'title': title,
            'publish_time': aware_datetime,
            'author': author,
            'source': source,
            'content': content_html,
            'news_tag_id': news_tag_id,
        }

    except Exception as e:
        print(f"An error occurred while processing {news_url}: {e}")
        return None

from celery import shared_task

@shared_task
def lj_main():
    # 行业新闻：http: // www.greenfinance.org.cn / more.php?cid = 70
    # 绿金新闻：http: // www.greenfinance.org.cn / more.php?cid = 71
    # http: // www.greenfinance.org.cn / more.php?cid = 71 & & page = 2
    base_url = 'http://www.greenfinance.org.cn/'
    categories = {
        "行业新闻": ("more.php?cid=70", 3),
        "绿金新闻": ("more.php?cid=71", 1),
        "绿金动态": ("more.php?cid=86", 2),
        "政策专题研究": ("more.php?cid=77", 2),
        "政策研究": ("more.php?cid=21", 2),
        "专题研究": ("more.php?cid=78", 4),
        "绿色案例国内": ("more.php?cid=73", 4),
        "绿色案例国内": ("more.php?cid=74", 4),
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

