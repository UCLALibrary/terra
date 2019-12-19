from django import template
from terra.utils import format_currency

register = template.Library()


@register.filter
def check_or_cross(bool):
    if bool == True:
        return '<span class="badge badge-pill badge-success">YES</span>'
    return '<span class="badge badge-pill badge-danger">NO</span>'


@register.filter
def currency(value):
    if value is None:
        value = 0
    return format_currency(value, grouping=True)
