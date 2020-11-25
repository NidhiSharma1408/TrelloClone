from django.urls import path,include
from . import views
from cards.views import CreateCardView
urlpatterns = [
    path('<int:list_id>/edit/',views.EditListView.as_view()),
    path('<int:list_id>/watch/',views.WatchUnwatchList.as_view()),
    path('<int:list_id>/cards/',CreateCardView.as_view()),
]