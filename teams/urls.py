from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . import views
router = DefaultRouter()
router.register(r'',views.TeamView)
urlpatterns = [
    path('',include(router.urls)),
    path('<int:id>/add/',views.AddTeamMemberView.as_view()),
    path('<int:id>/remove/',views.RemoveTeamMemberView.as_view()),
]