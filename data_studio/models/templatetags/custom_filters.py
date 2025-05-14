from django import template
from django.utils.timezone import now
from datetime import timedelta

register = template.Library()

@register.filter
def split(value, delimiter=","):
    """문자열을 특정 구분자로 나누는 템플릿 필터"""
    return value.split(delimiter) if value else []

@register.filter
def dict_get(d, key):
    return d.get(key, '')

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, str):
        return ""
    return dictionary.get(key)

@register.filter
def trim(value):
    return value.strip() if isinstance(value, str) else value

@register.filter
def time_since_short(value):
    """model.create_date로부터 얼마나 지났는지 간단하게 표현"""
    if not value:
        return ""

    delta = now() - value
    seconds = delta.total_seconds()

    if seconds < 60:
        return f"Updated about {int(seconds)} sec ago"
    elif seconds < 3600:
        return f"Updated about {int(seconds // 60)} min ago"
    elif seconds < 86400:
        return f"Updated about {int(seconds // 3600)} hours ago"
    elif seconds < 86400 * 30:
        return f"Updated {int(seconds // 86400)} days ago"
    else:
        return f"Updated on {value.strftime('%b %d, %Y')}"  # 예: May 07, 2024

@register.filter
def split(value: str, delimiter: str):
    """
    문자열을 delimiter 기준으로 분리한 리스트를 반환합니다.
    Usage in template: {{ value|split:"," }}
    """
    if not value:
        return []
    return [item.strip() for item in value.split(delimiter)]