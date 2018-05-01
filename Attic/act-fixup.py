from parliament.models import *
from django.db import transaction, reset_queries

if True:
    with transaction.atomic():
        print(("Documents %d" % Document.objects.count()))

        for idx, doc in enumerate(Document.objects.all()):
            if idx % 1000 == 0:
                reset_queries()
                print(idx)
            doc.keywords_changed = True
            doc.save(update_fields=['origin_id'])

if True:
    with transaction.atomic():
        print(("Signatures %d" % DocumentSignature.objects.count()))

        for idx, sign in enumerate(DocumentSignature.objects.all()):
            if idx % 1000 == 0:
                reset_queries()
                print(idx)
            sign.keywords_changed = True
            sign.save(update_fields=['doc'])

if True:
    with transaction.atomic():
        print(("Statements %d" % Statement.objects.count()))

        for idx, st in enumerate(Statement.objects.all()):
            if idx % 1000 == 0:
                reset_queries()
                print(idx)
            st.keywords_changed = True
            st.save(update_fields=['item'])
