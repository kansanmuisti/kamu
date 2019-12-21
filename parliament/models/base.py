import datetime

from django.db import models


class UpdatableModel(models.Model):
    last_modified_time = models.DateTimeField(null=True)
    last_checked_time = models.DateTimeField(null=True)

    def mark_modified(self):
        now = datetime.datetime.now()
        self.last_modified_time = now

    def mark_checked(self):
        now = datetime.datetime.now()
        self.last_checked_time = now

    class Meta:
        abstract = True
