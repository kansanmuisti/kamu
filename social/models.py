from django.db import models

class Tweet(models.Model):
    tweet_id = models.CharField(max_length=25, unique=True)
    user_id = models.CharField(max_length=25)
    text = models.CharField(max_length=140)
    created_at = models.DateTimeField(db_index=True)

class FacebookUpdate(models.Model):
    user_id = models.CharField(max_length=50)
    message = models.CharField(max_length=420)
    created_time = models.DateTimeField(db_index=True)

