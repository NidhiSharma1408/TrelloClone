from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . import views
from lists.views import CreateListView
router = DefaultRouter()
router.register(r'',views.BoardView)
urlpatterns = [
    path('',include(router.urls)),
    path('<int:id>/edit/members/',views.EditMembersInBoard.as_view()),
    path('<int:id>/star/',views.StarUnstarBoard.as_view()),
    path('<int:id>/watch/',views.WatchUnwatchBoard.as_view()),
    path('<int:id>/edit/admins/',views.MakeAdminOrRemoveFromAdmins.as_view()),
    path('<int:id>/lists/', CreateListView.as_view()),
]