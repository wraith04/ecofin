import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eco_fin.settings')  # 替换 myproject.settings 为你的实际项目设置路径
django.setup()
from django.core.cache import cache

def check_cached_recommendations(user_id):
    cache_key = f'user_recommendations_{user_id}'
    recommendations = cache.get(cache_key)
    if recommendations is not None:
        print(f"缓存命中：{recommendations}")
    else:
        print("缓存未命中或缓存已过期")

# 使用实际的 user_id 调用此函数
check_cached_recommendations(54)
