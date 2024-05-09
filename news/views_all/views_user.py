import pandas as pd
from django.contrib.auth.decorators import login_required
from django.db.models.functions import TruncDay
from django.shortcuts import redirect, render, get_object_or_404
from news.models import Tag, UserBehavior, News
from news.recommend_for_user import recommend_for_user
from django.contrib.auth import get_user_model
from django import forms
import plotly.express as px
from django.db.models import Count
User = get_user_model()
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'avatar']


import plotly.express as px
from django.db.models import Count

import plotly.express as px


def generate_category_pie_chart(user):
    # 假设的数据获取逻辑
    categories = UserBehavior.objects.filter(
        user=user,
        behavior_type='Read'
    ).values('news__news_tag__tag_name').annotate(total=Count('news__news_tag')).order_by('-total')

    # 绘制饼图
    fig = px.pie(
        categories,
        values='total',
        names='news__news_tag__tag_name',
        title='偏好的新闻类别',
        color_discrete_sequence=px.colors.sequential.RdBu,  # 使用预定义的颜色序列
        hole=0.3,  # 中间留白，制作环形图效果
    )

    # 布局调整
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        title=dict(x=0.5),  # 将标题居中
        font=dict(family="Arial, sans-serif", size=12, color="#333"),  # 调整字体
    )

    return fig.to_html(full_html=False)

import plotly.graph_objects as go


import pandas as pd
import plotly.graph_objects as go
from django.db.models.functions import TruncDay
from django.db.models import Count

def generate_behavior_time_series_chart(user):
    # 获取用户行为数据并按天和行为类型分组统计
    behaviors = user.userbehavior_set.annotate(day=TruncDay('behavior_time')).values('day', 'behavior_type').annotate(total=Count('id')).order_by('day')
    df = pd.DataFrame(list(behaviors))

    # 创建图表
    fig = go.Figure()

    # 检查是否有数据
    if not df.empty:
        # 对于每一种行为类型，添加一条线
        behavior_colors = {'Read': 'SkyBlue', 'Like': 'LightSalmon', 'Collect': 'Violet'}  # 预定义每种行为类型的颜色
        for behavior_type in df['behavior_type'].unique():
            df_behavior = df[df['behavior_type'] == behavior_type]
            color = behavior_colors.get(behavior_type, 'Gray')  # 获取行为类型对应的颜色，如果未定义则使用灰色
            fig.add_trace(go.Scatter(x=df_behavior['day'], y=df_behavior['total'],
                                     mode='lines+markers',
                                     name=behavior_type,
                                     line=dict(color=color, width=2),
                                     marker=dict(color=color, size=8, line=dict(width=2, color='DarkSlateGrey')),
                                     ))

    # 布局调整
    fig.update_layout(
        title='不同行为的次数统计',
        xaxis_title='日期',
        yaxis_title='次数',
        legend_title="行为类型",
        font=dict(family="Arial, sans-serif", size=12, color="#333"),  # 调整字体
        plot_bgcolor='white',  # 图表背景颜色
        paper_bgcolor='white',  # 整个画布的背景颜色
    )

    # 图表大小调整
    fig.update_layout(
        width=600,  # 调整宽度
        height=500,  # 调整高度
        margin=dict(l=50, r=50, t=50, b=50),  # 调整图表边距
    )

    # 增加网格线
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')

    return fig.to_html(full_html=False)
@login_required
def profile(request):
    tags = Tag.objects.all()
    search_query = request.GET.get('search_query')

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if u_form.is_valid():
            u_form.save()
            return redirect('profile')  # 重定向到资料页面

    else:
        u_form = UserUpdateForm(instance=request.user)

    # 根据有无搜索词来过滤用户的阅读、喜欢和收藏记录
    user_reads = UserBehavior.objects.filter(
        user=request.user,
        behavior_type='Read',
        news__title__icontains=search_query if search_query else ""
    ).select_related('news').order_by('-behavior_time')

    user_likes = UserBehavior.objects.filter(
        user=request.user,
        behavior_type='Like',
        news__title__icontains=search_query if search_query else ""
    ).select_related('news').order_by('-behavior_time')

    user_collects = UserBehavior.objects.filter(
        user=request.user,
        behavior_type='Collect',
        news__title__icontains=search_query if search_query else ""
    ).select_related('news').order_by('-behavior_time')

    if request.user.is_authenticated:
        user_id = request.user.id
        # 异步调用推荐系统函数
        recommended_news_ids =recommend_for_user(user_id)
        recommended_news = News.objects.filter(id__in=recommended_news_ids)
        category_pie_chart = generate_category_pie_chart(request.user)
        behavior_time_series_chart = generate_behavior_time_series_chart(request.user)
    else:
        recommended_news = News.objects.order_by('-reads')[:6]

    context = {
        'u_form': u_form,
        'user_reads': user_reads,
        'user_likes': user_likes,
        'user_collects': user_collects,
        'tags': tags,
        'recommended_news': recommended_news,
        'search_query': search_query,
        'category_pie_chart': category_pie_chart,
        'behavior_time_series_chart': behavior_time_series_chart
    }

    return render(request, 'registration/profile.html', context)


def delete_reading(request, behavior_id):
    behavior = get_object_or_404(UserBehavior, id=behavior_id, user=request.user, behavior_type='Read')
    behavior.delete()
    return redirect('profile')  # 假设你的用户资料页面的URL名称为'profile'


def delete_like(request, behavior_id):
    behavior = get_object_or_404(UserBehavior, id=behavior_id, user=request.user, behavior_type='Like')
    behavior.delete()
    return redirect('profile')  # 假设你的用户资料页面的URL名称为'profile'


def delete_collect(request, behavior_id):
    behavior = get_object_or_404(UserBehavior, id=behavior_id, user=request.user, behavior_type='Collect')
    behavior.delete()
    return redirect('profile')  # 假设你的用户资料页面的URL名称为'profile'


def edit_profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # 假设 'profile' 是展示用户资料的视图的名称
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'registration/edit_profile.html', {'form': form})

