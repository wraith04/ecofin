from django.core.paginator import Paginator
from django.shortcuts import render

from news.models import Tag, News
from news.recommend_for_user import recommend_for_user


def search_results(request):
    query = request.GET.get('query', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    tags = Tag.objects.all()
    # recommended_news = News.objects.order_by('-reads')[:6]  # Assuming recommendations are based on read counts
    if request.user.is_authenticated:
        user_id = request.user.id
        # 异步调用推荐系统函数
        recommended_news_ids = recommend_for_user(user_id)
        recommended_news = News.objects.filter(id__in=recommended_news_ids)
    else:
        recommended_news = News.objects.order_by('-reads')[:6]
    if query:
        search_results = News.objects.filter(title__icontains=query)
        if start_date:
            search_results = search_results.filter(publish_date__gte=start_date)
        if end_date:
            search_results = search_results.filter(publish_date__lte=end_date)
    else:
        # Provide an empty queryset instead of None
        search_results = News.objects.none()

    paginator = Paginator(search_results, 10)  # Display 10 news items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'search_results': search_results,
        'query': query,
        'start_date': start_date,
        'end_date': end_date,
        'tags': tags,
        'recommended_news': recommended_news,
        'page_obj': page_obj,
    }

    return render(request, 'registration/search_results.html', context)
