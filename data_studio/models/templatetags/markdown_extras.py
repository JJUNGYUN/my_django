import markdown
from django import template
from django.utils.safestring import mark_safe
from markdown.extensions.codehilite import CodeHiliteExtension
from pygments.formatters import HtmlFormatter

register = template.Library()
style = HtmlFormatter().get_style_defs('.codehilite')

@register.filter
def sub(value, arg):
    return value - arg

def convert_markdown_to_html(text):
    """
    Markdown을 HTML로 변환하며, 코드 하이라이팅을 적용
    """
    html = markdown.markdown(
        text, 
        extensions=["nl2br", "fenced_code", "toc","tables", CodeHiliteExtension(linenums=False)]
    )
    return f"{html}"

@register.filter
def mark(value):
    return convert_markdown_to_html(value)

# @register.filter
# def mark(value):
#     extensions = ["nl2br", "fenced_code", "tables", CodeHiliteExtension(linenums=False)]
#     style = HtmlFormatter().get_style_defs('.codehilite')

#     return f"<style>{style}</style> {mark_safe(markdown.markdown(value, extensions=extensions))}"

