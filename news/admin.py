from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from .models import SearchKeyword, News, Tag, Comment, UserBehavior, User
from django.utils.translation import gettext_lazy as _
# 已有的 SearchKeywordAdmin
@admin.register(SearchKeyword)
class SearchKeywordAdmin(admin.ModelAdmin):
    list_display = ('keyword',)
    search_fields = ('keyword',)

# 这里可以根据需要定义一个ModelAdmin类，来自定义admin界面的展示、过滤、搜索等功能
@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'publish_date', 'likes', 'reads')  # 在列表页显示的字段
    search_fields = ('title', 'content')  # 允许搜索的字段
    list_filter = ('publish_date', 'news_tag')  # 过滤器
    date_hierarchy = 'publish_date'  # 通过日期快速导航

# 注册News模型到admin界面

# 同样可以为其他模型注册，下面是一些示例：
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('tag_name',)
    search_fields = ('tag_name',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'news', 'comment_time')
    search_fields = ('content',)
    list_filter = ('comment_time',)
    date_hierarchy = 'comment_time'

@admin.register(UserBehavior)
class UserBehaviorAdmin(admin.ModelAdmin):
    list_display = ('user', 'news', 'behavior_type', 'behavior_time')
    list_filter = ('behavior_type', 'behavior_time')
    search_fields = ('user__username', 'news__title')

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # 定义额外的字段在admin的添加和更改页面上
    fieldsets = UserAdmin.fieldsets + (
        (_('Additional Info'), {'fields': ('user_type', 'avatar')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (_('Additional Info'), {'fields': ('user_type', 'avatar')}),
    )
    # 在用户列表页面显示额外的字段
    list_display = UserAdmin.list_display + ('user_type', 'email', 'avatar_display')
    # 添加过滤器
    list_filter = UserAdmin.list_filter + ('user_type',)

    def avatar_display(self, obj):
        """显示图片预览（如果有）"""
        if obj.avatar:
            return mark_safe(f'<img src="{obj.avatar.url}" width="30" height="30" />')
        return "-"
    avatar_display.short_description = "Avatar"