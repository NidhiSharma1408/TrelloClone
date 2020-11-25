from django.urls import path,include
from . import views
from checklists.views import CreateChecklistView
urlpatterns = [
    path('<int:card_id>/edit/',views.EditCardView.as_view()),
    path('<int:card_id>/watch/',views.WatchUnwatchCard.as_view()),
    path('<int:card_id>/checklists/',CreateChecklistView.as_view()),
    path('<int:card_id>/comments/',views.CommentView.as_view()),
    path('<int:card_id>/vote/',views.VoteCardView.as_view()),
    path('<int:card_id>/label/',views.CreateLabelView.as_view()),
    path('<int:card_id>/members/',views.EditMembersInCard.as_view()),
    path('<int:card_id>/attach/file/',views.AttachFileView.as_view()),
    path('<int:card_id>/attach/link/',views.AttachLinkView.as_view()),
]