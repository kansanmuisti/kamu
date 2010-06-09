from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _
from django.http import HttpResponseBadRequest
from PIL import Image
from StringIO import StringIO
import os
import tempfile

from kamu.orgs.models import Organization, SessionScore

def verify_logo_image(files, logo_path):
    f = files['logo']
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

    if logo_path:
        fn = os.path.join(settings.MEDIA_ROOT, self.logo_path)
        tmpf = (os.open(fn, os.O_WRONLY), fn)
    else:
        dir = os.path.join(settings.MEDIA_ROOT, settings.MEDIA_TMP_DIR)
        tmpf = tempfile.mkstemp(suffix='.png', dir=dir)
        # Make it readable by everyone
        os.chmod(tmpf[1], 0644)
    file = os.fdopen(tmpf[0], "w")
    image.save(file, "png")
    file.close()
    path = os.path.join(settings.MEDIA_TMP_DIR, os.path.basename(tmpf[1]))

    return path

class AddOrgForm(forms.Form):
    name = forms.CharField(max_length=50, label=_('Name'))
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
        self.logo_path = None
        if 'stored_logo' in self.data:
            s = self.data['stored_logo']
            # For a new organizations only valid stored_logo
            # is a preview logo temporary directory
            if not s.startswith(settings.MEDIA_TMP_DIR):
                raise forms.ValidationError(_("Invalid logo."))
            dir = os.path.join(settings.MEDIA_ROOT, s)
            if not os.access(dir, os.R_OK):
                raise HttpResponseBadRequest()
            self.logo_path = s
        if not 'logo' in self.files:
            # Logo is not required
            return
        self.logo_path = verify_logo_image(self.files, self.logo_path)

class ModifyOrgForm(AddOrgForm):
    def __init__(self, org, *args, **kwargs):
        self.org = org
        super(ModifyOrgForm, self).__init__(*args, **kwargs)

    def clean_name(self):
        s = self.cleaned_data['name']
        if len(s) < 2:
            raise forms.ValidationError(_("Not enough characters."))
        return s

    def clean_logo(self):
        self.logo_path = None
        orig_logo_path = self.org.logo
        # The case where no new logo is submitted on the form
        # It might be a temporary logo generated for preview though
        if 'stored_logo' in self.data and not 'logo' in self.files:
            s = self.data['stored_logo']
            # Logo must be a preview logo residing in temp still...
            if s.startswith(settings.MEDIA_TMP_DIR):
                dir = os.path.join(settings.MEDIA_ROOT, s)
            # ...or it must be the logo already stored in db for this org
            elif s == orig_logo_path:
                self.logo_path = s
                return
            else:
                raise forms.ValidationError(_("Invalid logo."))
            if not os.access(dir, os.R_OK):
                raise HttpResponseBadRequest()
            self.logo_path = s
        if not 'logo' in self.files:
            # This would be the removal of logo, but current UI
            # does not support this yet.
            return
        self.logo_path = verify_logo_image(self.files, self.logo_path)

class ModifyScoreForm(forms.ModelForm):
    class Meta:
        model = SessionScore
        fields = ('score', 'rationale')
