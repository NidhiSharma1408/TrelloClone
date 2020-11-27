from django.db import models
from boards.models import Board
from lists.models import List
from cards.models import Card
from userauth.models import UserProfile
# Create your models here.
class Activity(models.Model):
    description = models.TextField()
    time_created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(UserProfile,on_delete=models.DO_NOTHING,related_name='activity')
    board = models.ForeignKey(Board,on_delete=models.CASCADE,related_name="activity")
    list = models.ForeignKey(List,on_delete=models.CASCADE,related_name="activity")
    card = models.ForeignKey(Card,on_delete=models.CASCADE,realted_name="activity")