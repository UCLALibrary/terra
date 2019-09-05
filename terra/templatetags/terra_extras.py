from django import template
from terra.utils import format_currency

register = template.Library()


@register.filter
def check_or_cross(bool):
    if bool == True:
        return '<span class="badge badge-pill badge-success">&#10004;</span>'
    return '<span class="badge badge-pill badge-danger">&times;</span>'


@register.filter
def currency(value):
    return format_currency(value, grouping=True)
