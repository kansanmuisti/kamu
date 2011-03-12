from django.contrib import admin
from kamu.votes.models import Session, Vote, Member, County

class MemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'birth_date']

admin.site.register(Session)
admin.site.register(Vote)
admin.site.register(Member, MemberAdmin)
admin.site.register(County)
