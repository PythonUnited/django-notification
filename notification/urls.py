from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from notification.views import notices, mark_all_seen, feed_for_user, single, \
    notice_settings, \
    NoticeMarkSeenView, NoticeMarkUnseenView, NotificationRemoveView, \
    NoticeJSONDeleteView

urlpatterns = [
    url(r"^$", notices, name="notification_notices"),
    url(r"^settings/$", notice_settings, name="notification_notice_settings"),
    url(r"^(\d+)/$", single, name="notification_notice"),
    url(r"^feed/$", feed_for_user, name="notification_feed_for_user"),
    url(r"^mark_all_seen/$", mark_all_seen, name="notification_mark_all_seen"),


    # url(r"^notification_mark$",
    #     # login_required(NotificationMarkView.as_view()),
    #
    #     name="notification_mark"),

    url(r"^notice_delete/(?P<pk>[\d]+)/?",
        NoticeJSONDeleteView.as_view(),
        name="notifications_delete_notice_json"),

    url(r"^notice_mark_seen/(?P<pk>[\d]+)/?",
        login_required(NoticeMarkSeenView.as_view()),
        name="notice_mark_seen"),

    url(r"^notice_mark_unseen/(?P<pk>[\d]+)/?",
        login_required(NoticeMarkUnseenView.as_view()),
        name="notice_mark_unseen"),

    url(r"^notice_remove$",
        login_required(NotificationRemoveView.as_view()),
        name="notices_remove"),

]
