from django import template
from terra.utils import (
    format_currency,
    profdev_spending_cap,
    profdev_warning,
    profdev_days_cap,
    profdev_days_warning,
)
from datetime import date
from django.conf import settings

import fiscalyear as FY
import locale

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
    if value is None or value == "":
        value = 0
        return format_currency(value, grouping=True)
    # Over or at professional development cap
    if value >= profdev_spending_cap:
        return '<span class="alert-danger">{}</span>'.format(
            format_currency(value, grouping=True)
        )
    # Within 20% of professional development cap
    elif value >= profdev_warning and value < profdev_spending_cap:
        return '<span class="alert-warning">{}</span>'.format(
            format_currency(value, grouping=True)
        )
    else:
        return format_currency(value, grouping=True)


@register.filter
def days_cap(value):
    if value is None or value == "":
        value = 0
        return value
    # Over or at professional development cap
    if value >= profdev_days_cap:
        return '<span class="alert-danger">{}</span>'.format(value)
    # Within 20% of professional development cap
    elif value >= profdev_days_warning and value < profdev_days_cap:
        return '<span class="alert-warning">{}</span>'.format(value)
    else:
        return value
