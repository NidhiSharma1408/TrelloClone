from django.urls import path, include
from chat import views
urlpatterns = [
    path('<board_id>/', views.BoardChatView.as_view()),
]