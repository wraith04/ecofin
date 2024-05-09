from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# 设置Django的默认设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eco_fin.settings')

app = Celery('eco_fin')

# 从Django的设置文件中导入Celery设置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动从所有已注册的Django app中加载任务
app.autodiscover_tasks(['news'])
