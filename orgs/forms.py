from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _
from django.http import HttpResponseBadRequest
from PIL import Image
from StringIO import StringIO
import os
import tempfile

from kamu.orgs.models import Organization, SessionScore

class AddOrgForm(forms.Form):
    name = forms.CharField(max_length=30, label=_('Name'))
    description = forms.CharField(widget=forms.Textarea, label=_('Description'))
    info_link = forms.URLField(label=_('Home page link'))
    logo = forms.ImageField(required=False, label=_('Logo'))

    def clean_name(self):
        s = self.cleaned_data['name']
        if len(s) < 2:
            raise forms.ValidationError(_("Not enough characters."))
        try:
            org = Organization.objects.get(name = s)
            raise forms.ValidationError(_("Organization already exists."))
        except Organization.DoesNotExist:
            pass
        return s
    def clean_description(self):
        s = self.cleaned_data['description']
        if len(s) < 15:
            raise forms.ValidationError(_("Not enough characters."))
        return s
    def clean_logo(self):
        if not 'logo' in self.files:
            if 'stored_logo' in self.data:
                s = self.data['stored_logo']
                if not s.startswith(settings.MEDIA_TMP_DIR):
                    raise forms.ValidationError(_("Invalid logo."))
                dir = os.path.join(settings.MEDIA_ROOT, s)
                if not os.access(dir, os.R_OK):
                    raise HttpResponseBadRequest()
                self.logo_path = s
                return
            raise forms.ValidationError(_("Logo required."))
        f = self.files['logo']
        if f.size > 512*1024:
            raise forms.ValidationError(_("File size too big."))
        if hasattr(f, 'temporary_file_path'):
            file = f.temporary_file_path()
        else:
            if hasattr(f, 'read'):
                file = StringIO(f.read())
            else:
                file = StringIO(f['content'])

        image = Image.open(file)
        image.load()
        dim = max(image.size)
        if dim > 1024:
            raise forms.ValidationError(_("Image dimensions too big."))
        if dim > 500:
            factor = 500.0 / dim
            new_s = [int(d * factor + 0.5) for d in image.size]
            image = image.resize(new_s)
        dir = os.path.join(settings.MEDIA_ROOT, settings.MEDIA_TMP_DIR)
        tmpf = tempfile.mkstemp(suffix='.png', dir=dir)
        # Make it readable by everyone
        os.chmod(tmpf[1], 0644)
        file = os.fdopen(tmpf[0], "w")
        image.save(file, "png")
        file.close()
        path = os.path.join(settings.MEDIA_TMP_DIR, os.path.basename(tmpf[1]))
        self.logo_path = path

class ModifyScoreForm(forms.ModelForm):
    class Meta:
        model = SessionScore
        fields = ('score', 'rationale')
