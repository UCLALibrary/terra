import locale
from django import template

locale.setlocale(locale.LC_ALL, "")
register = template.Library()


@register.filter
def check_or_cross(bool):
    if bool == True:
        return '<span class="badge badge-pill badge-success">&#10004;</span>'
    return '<span class="badge badge-pill badge-danger">&times;</span>'


@register.filter
def currency(value):
    return locale.currency(value, grouping=True)
