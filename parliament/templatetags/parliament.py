from django import template
from ..models import Party, Statement

register = template.Library()

@register.filter(name='governing')
def governing(obj, date=None):
    if isinstance(obj, Party):
        assert date is not None, "Date must be supplied when 'govern' is called with a Party object"
        return obj.is_governing(date)
    elif isinstance(obj, Statement):
        if obj.member is None:
            if 'ministeri' in obj.speaker_role:
                return True
            else:
                return False
        if date is None:
            date = obj.item.plsess.date
        return obj.member.party.is_governing(date)
