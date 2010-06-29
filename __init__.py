from django.core.mail import mail_managers
from django.dispatch import dispatcher
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.contrib.comments.signals import comment_was_posted
from kamu.comments.models import KamuComment
import settings

def comment_notification(sender, comment, request, **kwargs):
    subject = 'New comment on %s' % str(comment.content_object)

    msg = u'Comment from: %s (%s)\n\n' % (comment.user_name, request.META['REMOTE_ADDR'])
    msg += u'Comment text:\n\n%s\n' % comment.comment

    mail_managers(subject, msg, fail_silently=True)

comment_was_posted.connect(comment_notification, sender=KamuComment)

def user_notification(sender, instance, **kwargs):
    if (not 'created' in kwargs) or (not kwargs['created']):
        return
    user = instance
    subject = u"New user '%s' created" % (user.username)

    msg = u"Email '%s'\n" % (user.email)

    mail_managers(subject, msg, fail_silently=True)

post_save.connect(user_notification, sender=User)
