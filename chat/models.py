from django.db import models
from userauth.models import UserProfile
from boards.models import Board

class Chat(models.Model):
    board    = models.ForeignKey(Board, related_name='chats', on_delete=models.CASCADE)
    sender  = models.ForeignKey(UserProfile, related_name='sent_messages', on_delete=models.CASCADE)
    text = models.TextField(blank=False)
    timestamp = models.DateTimeField(auto_now_add=True)