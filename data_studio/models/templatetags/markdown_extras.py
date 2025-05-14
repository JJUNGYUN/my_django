import markdown
from django import template
from django.utils.safestring import mark_safe
from markdown.extensions.codehilite import CodeHiliteExtension
from pygments.formatters import HtmlFormatter

import markdown_it
from markdown_it import MarkdownIt
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

register = template.Library()
style = HtmlFormatter().get_style_defs('.codehilite')

@register.filter
def sub(value, arg):
    return value - arg

def pygments_highlight(code, lang, attrs=None):
    try:
        lexer = get_lexer_by_name(lang)
        formatter = HtmlFormatter(nowrap=True)
        return highlight(code, lexer, formatter)
    except Exception:
        return f'<pre><code class="language-{lang}">{code}</code></pre>'

md = MarkdownIt("commonmark", {"highlight": pygments_highlight}).enable("fence").enable("table")

@register.filter(name='mark')
def markdown_to_html(text):
    html = md.render(text)
    return mark_safe(html)  # escape 제거

