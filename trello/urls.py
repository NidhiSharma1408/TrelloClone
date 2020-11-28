from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/',include('userauth.urls')),
    path('boards/',include('boards.urls')),
    path('lists/',include('lists.urls')),
    path('teams/',include('teams.urls')),
    path('cards/',include('cards.urls')),
    path('',include('checklists.urls')),
    path('chat/',include('chat.urls')),
    path('activity/',include('activity.urls')),
]+static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
