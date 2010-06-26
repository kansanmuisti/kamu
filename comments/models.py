from django.db import models
from django.contrib.comments.models import Comment as Comment
from django.contrib.auth.models import User

# Create your models here.
class KamuComment(Comment):
    """
    Customized comment class for kamu.
    """
