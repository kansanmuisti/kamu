import collections
import itertools

from django import forms
from django.utils.translation import ugettext as _
from django.utils.html import conditional_escape, mark_safe
from django.utils.encoding import force_unicode

CongruenceChoice = collections.namedtuple('CongruenceChoice', 'value name')
CONGRUENCE_CHOICES = (
    CongruenceChoice(-3, _('Incongruent')),
    CongruenceChoice(-2, _('Somewhat incongruent')),
    CongruenceChoice(-1, _('Slightly incongruent')),
    CongruenceChoice(0, _('Neutral/Irrelevant')),
    CongruenceChoice(1, _('Slightly congruent')),
    CongruenceChoice(2, _('Somewhat congruent')),
    CongruenceChoice(3, _('Congruent')),
)

class RadioInputWithSanerLabel:
    def __init__(self, parent):
        self.parent = parent

    def __getattr__(self, attr):
        return getattr(self.parent, attr)
    
    def __unicode__(self):
        if 'id' in self.attrs:
            label_for = ' for="%s_%s"' % (self.attrs['id'], self.index)
        else:
            label_for = ''
        
        choice_label = conditional_escape(force_unicode(self.choice_label))
        ret = mark_safe(u'<span title="%s">%s <label%s>%s</label></span>' % (
                   choice_label, self.tag(), label_for, choice_label))
        return ret


class RadioFieldRendererWithSanerLabels(forms.RadioSelect.renderer):
    def __iter__(self):
        insane_input = forms.RadioSelect.renderer.__iter__(self)
        while True: yield RadioInputWithSanerLabel(insane_input.next())

    def __getitem__(self, *args):
        insane_input = forms.RadioFieldRenderer.__getitem__(self, *args)
        return RadioInputWithSanerLabel(insane_input)
 
class VoteOptionCongruenceForm(forms.Form):
    congruence = forms.ChoiceField(choices=CONGRUENCE_CHOICES,
        widget=forms.RadioSelect(renderer=RadioFieldRendererWithSanerLabels),
        required=False)
