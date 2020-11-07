from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . import views
router = DefaultRouter()

router.register(r'teams',views.TeamView)
router.register(r'boards',views.BoardView)
urlpatterns = [
    path('',include(router.urls)),
    path('teams/<int:id>/add/',views.AddTeamMemberView.as_view()),
    path('teams/<int:id>/remove/',views.RemoveTeamMemberView.as_view()),
    path('boards/<int:id>/edit/members/',views.EditMembersInBoard.as_view()),
    path('boards/<int:id>/star/',views.StarUnstarBoard.as_view()),
    path('boards/<int:id>/watch/',views.WatchUnwatchBoard.as_view()),
    path('boards/<int:id>/edit/admins/',views.MakeAdminOrRemoveFromAdmins.as_view()),
    path('boards/<int:id>/lists/',views.CreateListView.as_view()),
    path('lists/<int:list_id>/edit/',views.EditListView.as_view()),
    path('lists/<int:list_id>/watch/',views.WatchUnwatchList.as_view()),
    path('lists/<int:list_id>/cards/',views.CreateCardView.as_view()),
    path('cards/<int:card_id>/edit/',views.EditCardView.as_view()),
    path('cards/<int:card_id>/watch/',views.WatchUnwatCard.as_view()),
    path('cards/<int:card_id>/checklists/',views.CreateChecklistView.as_view()),
    path('checklists/<int:checklist_id>/tasks/',views.CreateTaskView.as_view()),
    path('checklists/<int:checklist_id>/edit/',views.EditChecklistView.as_view()),
    path('tasks/<int:task_id>/edit/',views.TaskActionsView.as_view()),
    path('cards/<int:card_id>/comments/',views.AddCommentView.as_view()),
    path('cards/<int:card_id>/vote/',views.VoteCardView.as_view()),
]