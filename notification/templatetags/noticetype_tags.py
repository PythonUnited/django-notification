from django import template
from django.conf import settings
from notification.models import NoticeType, Notice

register = template.Library()

@register.simple_tag
def get_noticetypes_startingwith(txt):
    types = NoticeType.objects.filter(label__startswith=txt).values_list('pk', flat=True)
    return u",".join([str(i) for i in types])
    
@register.simple_tag
def get_noticetypes_in(labels):
    labels = labels.split(",")
    types = NoticeType.objects.filter(label__in=labels).values_list('pk', flat=True)
    return u",".join([str(i) for i in types])

@register.simple_tag()
def unseen_count_for(user):
    return Notice.objects.unseen_count_for(user)
