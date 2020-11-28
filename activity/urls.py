from django.urls import path,include

from . import views
urlpatterns = [
    path('board/<int:board_id>/',views.BoardActivity.as_view()),
    path('card/<int:card_id>/',views.CardActivity.as_view())
]