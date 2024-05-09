
from django import template
from django.utils.safestring import mark_safe
import re
register = template.Library()

@register.filter(name='times')
def times(value, arg):
    """Multiplies the value by the argument."""
    try:
        return value * arg
    except (ValueError, TypeError):
        return ''
@register.filter(name='highlight')
def highlight(text, query):
    highlighted = re.sub(f"({query})", r'<span style="background-color: #b7eb8f;">\1</span>', text, flags=re.IGNORECASE)
    return mark_safe(highlighted)

@register.filter
def strip_tags(value):
    """移除字符串中的HTML标签"""
    return re.sub(r'<[^>]+>', '', value)
@register.filter
def snippet(value, char_count=100):
    """截取前char_count个字符作为摘要"""
    value = strip_tags(value)  # 先移除HTML标签
    return value[:char_count] + '...' if len(value) > char_count else value
