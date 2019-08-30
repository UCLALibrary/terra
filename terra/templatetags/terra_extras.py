from django import template

register = template.Library()


@register.filter
def check_or_cross(bool):
    if bool == True:
        return '<span class="badge badge-pill badge-success">&#10004;</span>'
    return '<span class="badge badge-pill badge-danger">&times;</span>'
