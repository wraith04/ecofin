from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    # 如果需要添加额外的字段，可以在这里添加
    USER_TYPE_CHOICES = [
        ('Admin', '管理员'),
        ('RegisteredUser', '注册用户'),
    ]
    user_type = models.CharField(max_length=15, choices=USER_TYPE_CHOICES)  # 用户类型
    email = models.EmailField(blank=True, null=False, default='default@example.com')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)  # tuxiang
    # 新增邮箱验证字段
    # is_email_verified = models.BooleanField(default=False)  # 默认设置为False
    pass


class Tag(models.Model):
    tag_name = models.CharField(max_length=255, unique=True)
    # description = models.TextField(blank=True, null=True)  # 标签描述，可选


# 新闻模型
class News(models.Model):
    title = models.CharField(max_length=255)  # 新闻标题
    content = models.TextField()  # 新闻内容
    summary = models.TextField(blank=True, null=True)  # 新闻摘要，可选字段
    author = models.CharField(max_length=255, blank=True, null=True)  # 作者，可选
    publish_date = models.DateTimeField(default=timezone.now)  # 发布日期，默认为当前时间
    source = models.CharField(max_length=255, blank=True, null=True)  # 新闻来源，可选
    likes = models.IntegerField(default=0)  # 点赞数，默认为0
    reads = models.IntegerField(default=0)  # 阅读数，默认为0
    news_tag = models.ForeignKey(Tag, on_delete=models.CASCADE, null=True, blank=True)  # 标签ID，外键

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 用户ID，外键
    news = models.ForeignKey(News, on_delete=models.CASCADE)  # 新闻ID，外键
    content = models.TextField()  # 评论内容
    comment_time = models.DateTimeField(default=timezone.now)  # 评论时间，默认为当前时间

# 用户行为模型
class UserBehavior(models.Model):
    # 行为类型选项
    BEHAVIOR_TYPE_CHOICES = [
        ('Read', '阅读'),
        ('Like', '点赞'),
        ('Collect', '收藏'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 用户ID，外键
    news = models.ForeignKey(News, on_delete=models.CASCADE)  # 新闻ID，外键
    behavior_type = models.CharField(max_length=7, choices=BEHAVIOR_TYPE_CHOICES)  # 行为类型
    behavior_time = models.DateTimeField(default=timezone.now)  # 行为时间，默认为当前时间


# 个性化推荐模型
class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 用户ID，外键
    news = models.ForeignKey(News, on_delete=models.CASCADE)  # 新闻ID，外键
    score = models.FloatField()  # 推荐分数
    recommendation_time = models.DateTimeField(default=timezone.now)  # 推荐时间，默认为当前时间


# 访问日志模型
class AccessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 用户ID，外键
    access_time = models.DateTimeField(default=timezone.now)  # 访问时间，默认为当前时间
    ip_address = models.CharField(max_length=255)  # IP地址
    page_visited = models.CharField(max_length=255)  # 浏览的页面


# 管理员操作日志模型
class AdminActionLog(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE)  # 管理员ID，外键
    action_type = models.CharField(max_length=255)  # 操作类型
    action_description = models.TextField()  # 操作描述
    action_time = models.DateTimeField(default=timezone.now)  # 操作时间，默认为当前时间

#搜索关键词模型
class SearchKeyword(models.Model):
    keyword = models.CharField(max_length=255, unique=True, help_text="搜索关键词")
    updated_at = models.DateTimeField(auto_now=True)  # 自动设置为当前时间
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='search_keywords', help_text="关键词所属标签")



class DataCollectionTask(models.Model):
    STATUS_CHOICES = (
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('error', 'Error'),
    )
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_log = models.TextField(null=True, blank=True)
    collected_news = models.IntegerField(default=0)
