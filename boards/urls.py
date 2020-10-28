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
]