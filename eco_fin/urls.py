"""eco_fin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls')
"""
from django.contrib import admin
from django.contrib.auth.views import LogoutView, PasswordChangeView
from django.urls import path, include, reverse_lazy

from eco_fin import settings
from news.views_all import admin_views
from news.views_all.views_news import *
from news.views_all.views_user import *
from news.views_all.views_search import *
from news.views_all.views_auth import *
from django.conf.urls.static import static

urlpatterns = [
                  path("login/", user_login, name='login'),
                  path("register/", register, name='register'),
                  path('logout/', LogoutView.as_view(), name='logout'),  # 设置退出操作的URL
                  path('home/', home, name='home'),
                  path('news/<int:news_id>/', news_detail, name='news_detail'),
                  path('captcha/', include('captcha.urls')),
                  path('news/<int:news_id>/add_comment/', add_comment_to_news, name='add_comment_to_news'),
                  path('news/tag/<int:tag_id>/', news_by_tag, name='news_by_tag'),
                  path('profile/', profile, name='profile'),
                  path('change-password/', PasswordChangeView.as_view(
                      template_name='registration/change_password.html',
                      success_url=reverse_lazy('profile')  # 修改密码成功后重定向到用户资料页面
                  ), name='change_password'),
                  path('admin/', admin.site.urls),
                  path('news/<int:news_id>/like/', like_news, name='like_news'),
                  path('news/<int:news_id>/collet/', collect_news, name='collect_news'),
                  path('delete_reading/<int:behavior_id>/', delete_reading, name='delete_reading'),
                  path('delete_like/<int:behavior_id>/', delete_like, name='delete_like'),
                  path('delete_collect/<int:behavior_id>/', delete_collect, name='delete_collect'),
                  path('edit-profile/', edit_profile, name='edit_profile'),
                  path('search/', search_results, name='search_results'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
