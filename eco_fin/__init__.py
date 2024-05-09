# myproject/__init__.py
from __future__ import absolute_import, unicode_literals

# 这行代码将会使得 'celery.py' 文件中的设置生效
from .celery import app as celery_app

__all__ = ('celery_app',)
