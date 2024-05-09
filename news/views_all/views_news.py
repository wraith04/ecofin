from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from news.models import Tag, UserBehavior, News, Comment
from news.recommend_for_user import recommend_for_user


def news_detail(request, news_id):
    news = get_object_or_404(News, pk=news_id)
    likes_count = UserBehavior.objects.filter(news_id=news_id, behavior_type='Like').count()
    news.likes = likes_count
    # 增加阅读次数
    news.reads += 1
    news.save()

    tags = Tag.objects.all()
    if request.user.is_authenticated:
        user_id = request.user.id
        # 异步调用推荐系统函数
        recommended_news_ids = recommend_for_user(user_id)
        recommended_news = News.objects.filter(id__in=recommended_news_ids)
    else:
        recommended_news = News.objects.order_by('-reads')[:6]
    if request.user.is_authenticated:
        UserBehavior.objects.create(user=request.user, news=news, behavior_type='Read', behavior_time=timezone.now())
    # 处理评论提交
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login_url')  # 替换为实际的登录页面URL名称
        comment_content = request.POST.get('content', '')
        if comment_content:
            Comment.objects.create(user=request.user, news=news, content=comment_content)
            return redirect('news_detail', news_id=news_id)  # 重新加载页面以显示新评论

    return render(request, 'registration/news.detail.html', {
        'news': news,
        'recommended_news': recommended_news,
        'tags': tags,
    })


def like_news(request, news_id):
    news = get_object_or_404(News, pk=news_id)
    if request.user.is_authenticated:
        # 检查用户是否已经点赞
        if not UserBehavior.objects.filter(user=request.user, news=news, behavior_type='Like').exists():
            UserBehavior.objects.create(user=request.user, news=news, behavior_type='Like',
                                        behavior_time=timezone.now())
            # 这里可以增加逻辑来增加新闻的点赞计数，如果你的News模型中有这样的字段
            # news.likes_count += 1
            # news.save()
    return redirect('news_detail', news_id=news_id)  # 重新定向回新闻详情页面


def collect_news(request, news_id):
    news = get_object_or_404(News, pk=news_id)
    if request.user.is_authenticated:
        # 检查用户是否已经点赞
        if not UserBehavior.objects.filter(user=request.user, news=news, behavior_type='Collect').exists():
            UserBehavior.objects.create(user=request.user, news=news, behavior_type='Collect',
                                        behavior_time=timezone.now())
            # 这里可以增加逻辑来增加新闻的点赞计数，如果你的News模型中有这样的字段
            # news.likes_count += 1
            # news.save()
    return redirect('news_detail', news_id=news_id)  # 重新定向回新闻详情页面


@login_required
def add_comment_to_news(request, news_id):
    news = get_object_or_404(News, pk=news_id)
    if request.method == "POST":
        comment_content = request.POST.get("comment", "")
        if comment_content:
            Comment.objects.create(news=news, user=request.user, content=comment_content)
        # 重定向回新闻详情页面
        return redirect('news_detail', news_id=news_id)
    else:
        # 如果不是POST请求，也重定向回新闻详情页，或者显示一个错误页面
        return redirect('news_detail', news_id=news_id)


def news_by_tag(request, tag_id):
    tags = Tag.objects.all()
    current_tag_id = tag_id
    if request.user.is_authenticated:
        user_id = request.user.id
        # 异步调用推荐系统函数
        recommended_news_ids = recommend_for_user(user_id)
        recommended_news = News.objects.filter(id__in=recommended_news_ids)
    else:
        recommended_news = News.objects.order_by('-reads')[:6]
    tag1 = get_object_or_404(Tag, id=tag_id)
    # 然后使用这个标签的ID来过滤新闻
    news_list = News.objects.filter(news_tag=tag1)
    paginator = Paginator(news_list, 21)  # 每页显示10条新闻
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    print(current_tag_id)
    return render(request, 'registration/news_list_by_tag.html',
                  {'news_list': news_list, 'current_tag_id': current_tag_id, 'tag1': tag1, 'tags': tags,
                   'recommended_news': recommended_news, 'page_obj': page_obj})


def home(request):
    # 获取搜索关键词
    query = request.GET.get('q', '')
    if request.user.is_authenticated:
        user_id = request.user.id
        # 异步调用推荐系统函数
        recommended_news_ids = recommend_for_user(user_id)
        recommended_news = News.objects.filter(id__in=recommended_news_ids)
    else:
        recommended_news = News.objects.order_by('-reads')[:6]
    if query:
        # 如果有搜索请求，按标题搜索新闻
        all_news = News.objects.filter(title__icontains=query)
    else:
        # 否则获取所有新闻
        all_news = News.objects.all()

    # 最热新闻：按reads降序排序

    # 最新新闻：按发布日期降序排序
    latest_news = all_news.order_by('-publish_date')[:400]
    # 假设hottest_news是你的新闻列表
    hottest_news = all_news.order_by('-reads')[:6]  # 获取阅读量最高的6条新闻
    max_reads = hottest_news[0].reads if hottest_news else 0  # 获取最高阅读量

    # 为每条新闻计算高度比例（相对于最高阅读量）
    for news in hottest_news:
        news.height_ratio = (news.reads / max_reads) * 100 if max_reads else 0

    # 对最新新闻进行分页
    paginator = Paginator(latest_news, 20)  # 每页显示10条新闻
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    tags = Tag.objects.all()
    news_by_tag = {tag: News.objects.filter(news_tag=tag).order_by('-publish_date')[:9] for tag in tags}
    return render(request, 'registration/home.html', {
        'hottest_news': hottest_news,
        'page_obj': page_obj,
        'query': query,
        'tags': tags,
        'recommended_news': recommended_news,
        'news_by_tag': news_by_tag,
    })
