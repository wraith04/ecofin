from django.apps import AppConfig

class NewsConfig(AppConfig):
    name = 'news'

    def ready(self):
        from news.recommend_for_user import preload_resources
        # 调用预加载资源的函数
        preload_resources()