# import os
#
# from asgiref.sync import sync_to_async
# from django.core.signing import Signer, BadSignature
# from gensim.corpora import Dictionary
# from gensim.models import LdaModel
# from django import forms
# from django.shortcuts import render
# from django.core.paginator import Paginator
# from django.utils import timezone
# from django import forms
# from captcha.fields import CaptchaField
# from django.shortcuts import render, redirect
# from django.contrib.auth import authenticate, login
# from django import forms
# from transformers import DistilBertTokenizer, DistilBertModel
#
# from .models import User
# from .models import News, Comment
# from django.shortcuts import render, get_object_or_404
# from .models import News, Tag
# from django import forms
# from django.contrib.auth.models import User
# from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from .models import News  # 假设你用来记录阅读的模型名为News
# from django.shortcuts import get_object_or_404
# from news.models import News, UserBehavior
# from keras.models import load_model
# import numpy as np
#
# from .r12 import generate_user_representation_async, create_news_representation, create_category_feature_extractor
# from django.shortcuts import render
# from news.models import UserBehavior, News
# from keras.models import load_model
#
#
# # 假设模型已经被训练并保存
# remodel = '/Users/jiebaibai/Downloads/eco_fin/news/my_model.keras'
# keras_model = load_model(remodel)
# model_dir = '/Users/jiebaibai/Downloads/eco_fin/news/models_data'
# loaded_model = LdaModel.load(os.path.join(model_dir, 'lda_model.model'))
# loaded_dictionary = Dictionary.load(os.path.join(model_dir, 'lda_dictionary.dict'))
# tags = [tag.tag_name for tag in Tag.objects.all().order_by('id')]
# tag_model, tag_encoder = create_category_feature_extractor(tags)
# max_sequence_length = 100  # 最大序列长度
# news_vector_dimension = 794  # 新闻向量维度
# def recommend_for_user(user_id):
#     """
#     根据用户ID生成新闻推荐。
#     """
#     try:
#         # 检查是否有足够的用户历史行为
#         user_behaviors = UserBehavior.objects.filter(user=user_id)
#         if user_behaviors.count() < 20:
#             # 如果历史行为不足，返回基于阅读量的推荐
#             recommended_news = News.objects.order_by('-reads').values_list('id', flat=True)[:5]
#             return list(recommended_news)
#
#         # 生成用户表示
#         user_representation = await generate_user_representation_async(user_behaviors)
#
#         # 为所有新闻生成表示，并预测点击概率
#         predictions = []
#         for news in News.objects.all():
#             news_representation = create_news_representation(news)
#             prediction = keras_model.predict([user_representation, news_representation])[0][0]
#             predictions.append((news.id, prediction))
#
#         # 根据预测的点击概率排序，选出排名最高的新闻
#         predictions.sort(key=lambda x: x[1], reverse=True)
#         recommended_news_ids = [pred[0] for pred in predictions[:5]]
#
#         return recommended_news_ids
#     except Exception as e:
#         print(f"Error in recommend_for_user: {e}")
#         return []
#
# # 新闻详情页视图
# def news_detail(request, news_id):
#     news = get_object_or_404(News, pk=news_id)
#     likes_count = UserBehavior.objects.filter(news_id=news_id, behavior_type='Like').count()
#     news.likes = likes_count
#     # 增加阅读次数
#     news.reads += 1
#     news.save()
#
#     tags = Tag.objects.all()
#     if request.user.is_authenticated:
#         # 用户已登录，获取用户ID
#         user_id = request.user.id
#         # 调用个性化推荐函数
#         recommended_news_ids = recommend_for_user(user_id)
#         recommended_news = News.objects.filter(id__in=recommended_news_ids)
#     else:
#         # 用户未登录，根据阅读量和最新性推荐新闻
#         recommended_news = News.objects.order_by('-reads')[:6]
#     if request.user.is_authenticated:
#         UserBehavior.objects.create(user=request.user, news=news, behavior_type='Read', behavior_time=timezone.now())
#     # 处理评论提交
#     if request.method == 'POST':
#         if not request.user.is_authenticated:
#             return redirect('login_url')  # 替换为实际的登录页面URL名称
#         comment_content = request.POST.get('content', '')
#         if comment_content:
#             Comment.objects.create(user=request.user, news=news, content=comment_content)
#             return redirect('news_detail', news_id=news_id)  # 重新加载页面以显示新评论
#
#     return render(request, 'registration/news.detail.html', {
#         'news': news,
#         'recommended_news': recommended_news,
#         'tags': tags,
#     })
#
#
# from django.shortcuts import get_object_or_404, redirect
# from .models import News, UserBehavior
# from django.utils import timezone
#
#
# def like_news(request, news_id):
#     news = get_object_or_404(News, pk=news_id)
#     if request.user.is_authenticated:
#         # 检查用户是否已经点赞
#         if not UserBehavior.objects.filter(user=request.user, news=news, behavior_type='Like').exists():
#             UserBehavior.objects.create(user=request.user, news=news, behavior_type='Like',
#                                         behavior_time=timezone.now())
#             # 这里可以增加逻辑来增加新闻的点赞计数，如果你的News模型中有这样的字段
#             # news.likes_count += 1
#             # news.save()
#     return redirect('news_detail', news_id=news_id)  # 重新定向回新闻详情页面
#
#
# def collect_news(request, news_id):
#     news = get_object_or_404(News, pk=news_id)
#     if request.user.is_authenticated:
#         # 检查用户是否已经点赞
#         if not UserBehavior.objects.filter(user=request.user, news=news, behavior_type='Collect').exists():
#             UserBehavior.objects.create(user=request.user, news=news, behavior_type='Collect',
#                                         behavior_time=timezone.now())
#             # 这里可以增加逻辑来增加新闻的点赞计数，如果你的News模型中有这样的字段
#             # news.likes_count += 1
#             # news.save()
#     return redirect('news_detail', news_id=news_id)  # 重新定向回新闻详情页面
#
#
# def home(request):
#     # 获取搜索关键词
#     query = request.GET.get('q', '')
#     if request.user.is_authenticated:
#         # 用户已登录，获取用户ID
#         user_id = request.user.id
#         # 调用个性化推荐函数
#         recommended_news_ids = recommend_for_user(user_id)
#         recommended_news = News.objects.filter(id__in=recommended_news_ids)
#     else:
#         # 用户未登录，根据阅读量和最新性推荐新闻
#         recommended_news = News.objects.order_by('-reads')[:6]
#     if query:
#         # 如果有搜索请求，按标题搜索新闻
#         all_news = News.objects.filter(title__icontains=query)
#     else:
#         # 否则获取所有新闻
#         all_news = News.objects.all()
#
#     # 最热新闻：按reads降序排序
#
#     # 最新新闻：按发布日期降序排序
#     latest_news = all_news.order_by('-publish_date')[:400]
#     # 假设hottest_news是你的新闻列表
#     hottest_news = all_news.order_by('-reads')[:6]  # 获取阅读量最高的6条新闻
#     max_reads = hottest_news[0].reads if hottest_news else 0  # 获取最高阅读量
#
#     # 为每条新闻计算高度比例（相对于最高阅读量）
#     for news in hottest_news:
#         news.height_ratio = (news.reads / max_reads) * 100 if max_reads else 0
#
#     # 对最新新闻进行分页
#     paginator = Paginator(latest_news, 20)  # 每页显示10条新闻
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#     tags = Tag.objects.all()
#     news_by_tag = {tag: News.objects.filter(news_tag=tag).order_by('-publish_date')[:9] for tag in tags}
#     # tags = Tag.objects.all().order_by('category')
#     # print(tags)
#     return render(request, 'registration/home.html', {
#         'hottest_news': hottest_news,
#         'page_obj': page_obj,
#         'query': query,
#         'tags': tags,
#         'recommended_news': recommended_news,
#         'news_by_tag':news_by_tag,
#     })
#
#
# class LoginForm(forms.Form):
#     username = forms.CharField(label='用户名', max_length=100)
#     password = forms.CharField(label='密码', widget=forms.PasswordInput)
#     captcha = CaptchaField(label='验证码')
#
#
# from django.http import HttpResponseRedirect
#
#
# def user_login(request):
#     next_url = request.GET.get('next', 'home')  # 尝试从GET请求中获取'next'参数，如果没有，则默认为'home'
#     if request.method == 'POST':
#         form = LoginForm(request.POST)
#         if form.is_valid():
#             username = form.cleaned_data['username']
#             password = form.cleaned_data['password']
#             user = authenticate(request, username=username, password=password)
#             if user is not None:
#                 login(request, user)
#                 return HttpResponseRedirect(next_url)  # 使用重定向到'next_url'
#             else:
#                 form.add_error(None, '用户名或密码不正确')
#     else:
#         form = LoginForm()
#     return render(request, 'registration/login.html', {'form': form, 'next': next_url})
#
#
# from django.contrib.auth import get_user_model
#
# User = get_user_model()
#
#
# class RegisterForm(forms.ModelForm):
#     password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="密码")
#     password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="确认密码")
#
#     class Meta:
#         model = User
#         fields = ('username', 'email')  # 移除'user_type'
#         widgets = {
#             'username': forms.TextInput(attrs={'class': 'form-control'}),
#             'email': forms.EmailInput(attrs={'class': 'form-control'}),
#         }
#         error_messages = {
#             'username': {
#                 'required': "用户名是必填项。",
#                 'max_length': "用户名不能超过150个字符。",
#                 'invalid': "用户名只能包含字母、数字以及 @/./+/-/_ 符号。",
#             },
#             'email': {
#                 'required': "电子邮件是必填项。",
#                 'invalid': "请输入一个有效的电子邮件地址。",
#             },
#             # 如果有其他字段的自定义错误消息也可以在这里添加
#         }
#
#     def clean_username(self):
#         username = self.cleaned_data['username']
#         if User.objects.filter(username=username).exists():
#             raise forms.ValidationError("该用户名已被占用，请选择其他用户名。")
#         return username
#     def clean_password2(self):
#         cd = self.cleaned_data
#         if cd['password'] != cd['password2']:
#             raise forms.ValidationError('密码不匹配。')
#         return cd['password2']
# def register(request):
#     next_url = request.GET.get('next', 'home')  # 尝试从GET请求中获取'next'参数，如果没有，则默认为'home'
#     if request.method == 'POST':
#         user_form = RegisterForm(request.POST)
#         if user_form.is_valid():
#             # 创建但不保存新用户记录
#             new_user = user_form.save(commit=False)
#             # 设置密码
#             new_user.set_password(user_form.cleaned_data['password'])
#             # 设置用户类型为"RegisteredUser"
#             new_user.user_type = 'RegisteredUser'
#             # 保存用户
#             new_user.save()
#             return HttpResponseRedirect(next_url)  # 重定向到 'next_url'
#     else:
#         user_form = RegisterForm()
#         print(user_form)
#     return render(request, 'registration/register.html', {'user_form': user_form})
#
#
# class UserUpdateForm(forms.ModelForm):
#     email = forms.EmailField()
#
#     class Meta:
#         model = User
#         fields = ['username', 'email', 'avatar']
#
#
#
# @login_required
# def profile(request):
#     tags = Tag.objects.all()
#     search_query = request.GET.get('search_query')
#
#     if request.method == 'POST':
#         u_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
#         if u_form.is_valid():
#             u_form.save()
#             return redirect('profile')  # 重定向到资料页面
#
#     else:
#         u_form = UserUpdateForm(instance=request.user)
#
#     # 根据有无搜索词来过滤用户的阅读、喜欢和收藏记录
#     user_reads = UserBehavior.objects.filter(
#         user=request.user,
#         behavior_type='Read',
#         news__title__icontains=search_query if search_query else ""
#     ).select_related('news').order_by('-behavior_time')
#
#     user_likes = UserBehavior.objects.filter(
#         user=request.user,
#         behavior_type='Like',
#         news__title__icontains=search_query if search_query else ""
#     ).select_related('news').order_by('-behavior_time')
#
#     user_collects = UserBehavior.objects.filter(
#         user=request.user,
#         behavior_type='Collect',
#         news__title__icontains=search_query if search_query else ""
#     ).select_related('news').order_by('-behavior_time')
#
#     if request.user.is_authenticated:
#         # 用户已登录，获取用户ID
#         user_id = request.user.id
#         # 调用个性化推荐函数
#         recommended_news_ids = recommend_for_user(user_id)
#         recommended_news = News.objects.filter(id__in=recommended_news_ids)
#     else:
#         # 用户未登录，根据阅读量和最新性推荐新闻
#         recommended_news = News.objects.order_by('-reads')[:6]
#
#     context = {
#         'u_form': u_form,
#         'user_reads': user_reads,
#         'user_likes': user_likes,
#         'user_collects': user_collects,
#         'tags': tags,
#         'recommended_news': recommended_news,
#         'search_query': search_query,
#     }
#
#     return render(request, 'registration/profile.html', context)
#
#
# def delete_reading(request, behavior_id):
#     behavior = get_object_or_404(UserBehavior, id=behavior_id, user=request.user, behavior_type='Read')
#     behavior.delete()
#     return redirect('profile')  # 假设你的用户资料页面的URL名称为'profile'
#
#
# def delete_like(request, behavior_id):
#     behavior = get_object_or_404(UserBehavior, id=behavior_id, user=request.user, behavior_type='Like')
#     behavior.delete()
#     return redirect('profile')  # 假设你的用户资料页面的URL名称为'profile'
#
#
# def delete_collect(request, behavior_id):
#     behavior = get_object_or_404(UserBehavior, id=behavior_id, user=request.user, behavior_type='Collect')
#     behavior.delete()
#     return redirect('profile')  # 假设你的用户资料页面的URL名称为'profile'
#
#
# def edit_profile(request):
#     if request.method == 'POST':
#         form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
#         if form.is_valid():
#             form.save()
#             return redirect('profile')  # 假设 'profile' 是展示用户资料的视图的名称
#     else:
#         form = UserUpdateForm(instance=request.user)
#
#     return render(request, 'registration/edit_profile.html', {'form': form})
#
#
# @login_required
# def add_comment_to_news(request, news_id):
#     news = get_object_or_404(News, pk=news_id)
#     if request.method == "POST":
#         comment_content = request.POST.get("comment", "")
#         if comment_content:
#             Comment.objects.create(news=news, user=request.user, content=comment_content)
#         # 重定向回新闻详情页面
#         return redirect('news_detail', news_id=news_id)
#     else:
#         # 如果不是POST请求，也重定向回新闻详情页，或者显示一个错误页面
#         return redirect('news_detail', news_id=news_id)
#
#
# def news_by_tag(request, tag_id):
#     tags = Tag.objects.all()
#     current_tag_id = tag_id
#     if request.user.is_authenticated:
#         # 用户已登录，获取用户ID
#         user_id = request.user.id
#         # 调用个性化推荐函数
#         recommended_news_ids = recommend_for_user(user_id)
#         recommended_news = News.objects.filter(id__in=recommended_news_ids)
#     else:
#         # 用户未登录，根据阅读量和最新性推荐新闻
#         recommended_news = News.objects.order_by('-reads')[:6]
#     tag1 = get_object_or_404(Tag, id=tag_id)
#     # 然后使用这个标签的ID来过滤新闻
#     news_list = News.objects.filter(news_tag=tag1)
#     paginator = Paginator(news_list, 21)  # 每页显示10条新闻
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#     print(current_tag_id)
#     return render(request, 'registration/news_list_by_tag.html',
#                   {'news_list': news_list, 'current_tag_id': current_tag_id, 'tag1': tag1, 'tags': tags,
#                    'recommended_news': recommended_news, 'page_obj': page_obj})
#
#
# def search_results(request):
#     query = request.GET.get('query', '')
#     start_date = request.GET.get('start_date', '')
#     end_date = request.GET.get('end_date', '')
#     tags = Tag.objects.all()
#     # recommended_news = News.objects.order_by('-reads')[:6]  # Assuming recommendations are based on read counts
#     if request.user.is_authenticated:
#         # 用户已登录，获取用户ID
#         user_id = request.user.id
#         # 调用个性化推荐函数
#         recommended_news_ids = recommend_for_user(user_id)
#     else:
#         # 用户未登录，根据阅读量和最新性推荐新闻
#         recommended_news_ids = News.objects.order_by('-reads').values_list('id', flat=True)[:6]
#     recommended_news = News.objects.filter(id__in__in=recommended_news_ids)
#     if query:
#         search_results = News.objects.filter(title__icontains=query)
#         if start_date:
#             search_results = search_results.filter(publish_date__gte=start_date)
#         if end_date:
#             search_results = search_results.filter(publish_date__lte=end_date)
#     else:
#         # Provide an empty queryset instead of None
#         search_results = News.objects.none()
#
#     paginator = Paginator(search_results, 10)  # Display 10 news items per page
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#
#     context = {
#         'search_results': search_results,
#         'query': query,
#         'start_date': start_date,
#         'end_date': end_date,
#         'tags': tags,
#         'recommended_news': recommended_news,
#         'page_obj': page_obj,
#     }
#
#     return render(request, 'registration/search_results.html', context)
