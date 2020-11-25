from django.urls import path,include
from cards.views import EditDeleteAttachedFileView,EditDeleteAttachedLinkView,EditDeleteLabelView
from . import views
urlpatterns = [
    path('checklists/<int:checklist_id>/tasks/',views.CreateTaskView.as_view()),
    path('checklists/<int:checklist_id>/edit/',views.EditChecklistView.as_view()),
    path('tasks/<int:task_id>/edit/',views.TaskActionsView.as_view()),
    path('attach/link/<int:id>/',EditDeleteAttachedLinkView.as_view()),
    path('attach/file/<int:id>/',EditDeleteAttachedFileView.as_view()),
    path('labels/<int:id>/',EditDeleteLabelView.as_view())
]