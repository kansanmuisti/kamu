from django import template

register = template.Library()

@register.filter(name='governing')
def governing(party, date):
    return party.is_governing(date)

