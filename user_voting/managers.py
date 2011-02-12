from django.conf import settings
from django.db import connection, models
from django.contrib.contenttypes.models import ContentType


class VoteManager(models.Manager):
    def get_count(self, obj, score):
        ctype = ContentType.objects.get_for_model(obj)
        q = self.filter(object_id=obj._get_pk_val(), content_type=ctype,
                        score=score)
        return q.count()

    def record_vote(self, obj, user, score):
        ctype = ContentType.objects.get_for_model(obj)
        try:
            v = self.get(user=user, content_type=ctype,
                         object_id=obj._get_pk_val())
            if score == None:
                v.delete()
            else:
                v.score = score
                v.save()
        except models.ObjectDoesNotExist:
            if score != None:
                self.create(user=user, content_type=ctype,
                            object_id=obj._get_pk_val(), score=score)
