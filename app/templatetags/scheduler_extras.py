from django import template

register = template.Library()


@register.filter
def attr(obj: object, name: str) -> object:
    return getattr(obj, name)
