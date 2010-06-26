from django import forms
from django.contrib.comments.forms import CommentForm
from kamu.comments.models import KamuComment

class KamuCommentForm(CommentForm):
    email = forms.EmailField(required=False)

    def get_comment_model(self):
        # Use our custom comment model instead of the built-in one.
        return KamuComment

    def get_comment_create_data(self):
        # Use the data of the superclass, and add in the title field
        data = super(KamuCommentForm, self).get_comment_create_data()
        return data

