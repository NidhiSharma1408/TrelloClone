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
    path('boards/<int:board_id>/lists/<int:list_id>/edit/',views.EditListView.as_view()),
    path('boards/<int:board_id>/lists/<int:list_id>/watch/',views.WatchUnwatchList.as_view()),

]