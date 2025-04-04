from django import template

register = template.Library()

@register.filter
def split(value, delimiter=","):
    """문자열을 특정 구분자로 나누는 템플릿 필터"""
    return value.split(delimiter) if value else []
