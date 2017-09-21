import json

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, Http404, HttpResponse

from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView
from django.views.generic import View
from django.views.generic.edit import BaseDeleteView

from notification.models import *
from notification.decorators import basic_auth_required, simple_basic_auth_callback
from notification.feeds import NoticeUserFeed


@basic_auth_required(realm="Notices Feed", callback_func=simple_basic_auth_callback)
def feed_for_user(request):
    """
    An atom feed for all :model:`notification.Notice`s for a user.
    """
    feedgen = NoticeUserFeed().get_feed(request.user.username)
    response = HttpResponse(mimetype=feedgen.mime_type)
    feedgen.write(response, 'utf-8')
    return response


@login_required
def notices(request):
    """
    The main notices index view.
    
    Template: :template:`notification/notices.html`
    
    Context:
    
        notices
            A list of :model:`notification.Notice` to be displayed on the site.
        
        only_show
            A list of filters corresponding to :model:`notification.NoticeType`
            labels, if present in ``request.GET``
    """
    notices = Notice.objects.notices_for(request.user, on_site=True)
    
    if 'only_show' in request.GET:
        only_show = request.GET['only_show'].split(',')
        notices = notices.filter(notice_type__in=only_show)            
    else:
        only_show = None

    return render(request, 'notification/notices.html', {
        "notices": notices,
        "only_show": only_show,
    })

    
@login_required
def notice_settings(request):
    """
    The notice settings view.
    
    Template: :template:`notification/notice_settings.html`
    
    Context:
        
        notice_types
            A list of all :model:`notification.NoticeType` objects.
        
        notice_settings
            A dictionary containing ``column_headers`` for each ``NOTICE_MEDIA``
            and ``rows`` containing a list of dictionaries: ``notice_type``, a
            :model:`notification.NoticeType` object and ``cells``, a list of
            tuples whose first value is suitable for use in forms and the second
            value is ``True`` or ``False`` depending on a ``request.POST``
            variable called ``form_label``, whose valid value is ``on``.
    """
    notice_types = NoticeType.objects.all()
    settings_table = []
    for notice_type in notice_types:
        settings_row = []
        for medium_id, medium_display in NOTICE_MEDIA:
            form_label = "%s_%s" % (notice_type.label, medium_id)
            setting = get_notification_setting(request.user, notice_type, medium_id)
            if request.method == "POST":
                if request.POST.get(form_label) == "on":
                    if not setting.send:
                        setting.send = True
                        setting.save()
                else:
                    if setting.send:
                        setting.send = False
                        setting.save()
            settings_row.append((form_label, setting.send))
        settings_table.append({"notice_type": notice_type, "cells": settings_row})
    
    if request.method == "POST":
        next_page = request.POST.get("next_page", ".")
        return HttpResponseRedirect(next_page)
    
    notice_settings = {
        "column_headers": [medium_display for medium_id, medium_display in NOTICE_MEDIA],
        "rows": settings_table,
    }
    
    return render(request, "notification/notice_settings.html", {
        "notice_types": notice_types,
        "notice_settings": notice_settings,
    })


@login_required
def single(request, id, mark_seen=True):
    """
    Detail view for a single :model:`notification.Notice`.
    
    Template: :template:`notification/single.html`
    
    Context:
    
        notice
            The :model:`notification.Notice` being viewed
    
    Optional arguments:
    
        mark_seen
            If ``True``, mark the notice as seen if it isn't
            already.  Do nothing if ``False``.  Default: ``True``.
    """
    notice = get_object_or_404(Notice, id=id)
    if request.user == notice.recipient:
        if mark_seen and notice.unseen:
            notice.unseen = False
            notice.save()
        return render(request, "notification/single.html", {
            "notice": notice,
        })
    raise Http404


@login_required
def archive(request, noticeid=None, next_page=None):
    """
    Archive a :model:`notices.Notice` if the requesting user is the
    recipient or if the user is a superuser.  Returns a
    ``HttpResponseRedirect`` when complete.
    
    Optional arguments:
    
        noticeid
            The ID of the :model:`notices.Notice` to be archived.
        
        next_page
            The page to redirect to when done.
    """
    if noticeid:
        try:
            notice = Notice.objects.get(id=noticeid)
            if request.user == notice.recipient or request.user.is_superuser:
                notice.archive()
            else:   # you can archive other users' notices
                    # only if you are superuser.
                return HttpResponseRedirect(next_page)
        except Notice.DoesNotExist:
            return HttpResponseRedirect(next_page)
    return HttpResponseRedirect(next_page)


# @login_required
# def delete(request, noticeid=None, next_page=None):
#     """
#     Delete a :model:`notices.Notice` if the requesting user is the recipient
#     or if the user is a superuser.  Returns a ``HttpResponseRedirect`` when
#     complete.
#
#     Optional arguments:
#
#         noticeid
#             The ID of the :model:`notices.Notice` to be archived.
#
#         next_page
#             The page to redirect to when done.
#     """
#     if not next_page:
#         next_page = request.path
#
#     if noticeid:
#         try:
#             notice = Notice.objects.get(id=noticeid)
#             if request.user == notice.recipient or request.user.is_superuser:
#                 notice.delete()
#             else:   # you can delete other users' notices
#                     # only if you are superuser.
#                 return HttpResponseRedirect(next_page)
#         except Notice.DoesNotExist:
#             return HttpResponseRedirect(next_page)
#     return HttpResponseRedirect(next_page)
#

@login_required
def mark_all_seen(request):
    """
    Mark all unseen notices for the requesting user as seen.  Returns a
    ``HttpResponseRedirect`` when complete. 
    """
    
    Notice.objects.notices_for(request.user, unseen=True).update(unseen=False)
    return HttpResponseRedirect(reverse("notification_notices"))


class NoticeMarkSeenView(DetailView):

    template_name = "notification/snippets/notice.html"
    model = Notice
    content_type = "text/plain"

    def get(self, request, *args, **kwargs):

        self.object = self.get_object()

        self.object.unseen = False
        self.object.save()

        return super(NoticeMarkSeenView, self).get(request, *args, **kwargs)


class NoticeMarkUnseenView(DetailView):

    template_name = "notification/snippets/notice.html"
    model = Notice
    content_type = "text/plain"

    def get(self, request, *args, **kwargs):

        self.object = self.get_object()

        self.object.unseen = True
        self.object.save()

        return super(NoticeMarkUnseenView, self).get(request, *args, **kwargs)


class NotificationMixin(object):

    def get_object(self, queryset=None):

        return self.request.user.get_profile

    def get_context_data(self, **kwargs):

        return {
            "notices": Notice.objects.notices_for(self.request.user,
                                                  on_site=True)
        }


class JSONResponseMixin(object):

    template_name = None

    def render_html(self, context, template=None):

        """ Override this so as to return an actual html
        template. This will be added to the JSON data under the key of
        'html'.
        """

        if not template:
            template = self.template_name

        return template and render_to_string(template, context) or ""

    def get_context_data(self, **kwargs):

        """ Base implementation that just returns the view's kwargs """


        kwargs['request'] = self.request

        return kwargs


    def render_to_response(self, context, template=None, **response_kwargs):
        "Returns a JSON response containing 'context' as payload"

        context['html'] = self.render_html(context, template=template)

        return HttpResponse(
            json.dumps(context, skipkeys=True,
                       default=lambda x: "NOT SERIALIZABLE"),
            content_type='application/json',
            **response_kwargs)


class InlineActionMixin(JSONResponseMixin):

    """ Handle action in a JSON way.
    """

    handle_on_get = False
    handle_on_post = True

    def handle_request(self, *args, **kwargs):

        """ Implement handle call to actually do something... Must
        return a tuple of (status, errors) """

        raise NotImplementedError

    def get(self, request, *args, **kwargs):

        if self.handle_on_get:
            kwargs['status'], kwargs['errors'] = self.handle_request()
        else:
            kwargs['status'] = 0
            kwargs['errors'] = ""

        return self.render_to_response(self.get_context_data(**kwargs))


    def post(self, request, *args, **kwargs):
        if self.handle_on_post:
            kwargs['status'], kwargs['errors'] = self.handle_request()
        else:
            kwargs['status'] = 0
            kwargs['errors'] = ""

        return self.render_to_response(self.get_context_data(**kwargs))


class NotificationRemoveView(InlineActionMixin, NotificationMixin, View):

    template_name = "notification/notices_block.html"
    handle_on_get = True

    def get_context_data(self, **kwargs):

        data = InlineActionMixin.get_context_data(self, **kwargs)
        data.update(NotificationMixin.get_context_data(self, **kwargs))

        return data

    def handle_request(self):

        """ Add or remove relation"""

        ids = self.request.POST.getlist("ids[]")

        if ids:
            Notice.objects.notices_for(
                self.request.user,
                on_site=True).filter(id__in=ids).delete()

        return 0, ""


class NotificationToggleSeenView(InlineActionMixin, NotificationMixin, View):

    template_name = "notification/notices_block.html"
    handle_on_get = True

    def get_context_data(self, **kwargs):

        data = InlineActionMixin.get_context_data(self, **kwargs)
        data.update(NotificationMixin.get_context_data(self, **kwargs))

        return data

    def handle_request(self):

        """ Add or remove relation"""

        ids = self.request.POST.getlist("ids[]")

        if ids:
            for notice in Notice.objects.notices_for(
                    self.request.user, on_site=True).filter(id__in=ids):
                notice.unseen = not notice.unseen
                notice.save()

        return 0, ""


class JSONDeleteView(JSONResponseMixin, BaseDeleteView):

    def get_context_data(self, **kwargs):

        return {'status': 0, 'errors': {}}

    def post(self, *args, **kwargs):

        self.object = self.get_object()
        self.object.delete()

        context = self.get_context_data(**kwargs)

        return self.render_to_response(context)


class NoticeJSONDeleteView(JSONDeleteView):

    model = Notice
