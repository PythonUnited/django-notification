# -*- coding:utf-8 -*-
from time import time
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from notification.models import Notice


class Command(BaseCommand):
    """Remove old notices"""
    help = __doc__

    def add_arguments(self, parser):

        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dryrun',
            default=False,
            help='Count the number of elements that would be deleted, without actually doing it'
        )

    def handle(self, *args, **options):
        dryrun = options['dryrun']
        limit = time() - settings.NOTICES_MAX_AGE
        limit = datetime.fromtimestamp(limit)
        notices = Notice.objects.filter(added__lte=limit)
        if dryrun:
            count = notices.count()
            print('Total count of notices to be deleted: %d' % count)
        else:
            notices.delete()


