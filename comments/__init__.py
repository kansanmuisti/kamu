from kamu.comments.models import KamuComment
from kamu.comments.forms import KamuCommentForm

def get_model():
    return KamuComment

def get_form():
    return KamuCommentForm
