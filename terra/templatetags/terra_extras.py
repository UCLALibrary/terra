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
    if value is None or value == "":
        value = 0
    return format_currency(value, grouping=True)


@register.filter
def cap(value):
    if value >= 3500:
        return '<span class="badge badge-pill badge-danger">{}</span>'.format(value)
    elif value >= 2800:
        return '<span class="badge badge-pill badge-warning">{}</span>'.format(value)
    else:
        return value
