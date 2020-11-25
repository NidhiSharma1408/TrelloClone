from django.db import models
from userauth.models import UserProfile
from boards.models import Board
# Create your models here.

class List(models.Model):
    board = models.ForeignKey(Board,on_delete=models.CASCADE,related_name='lists')
    name = models.CharField(max_length=250)
    watched_by = models.ManyToManyField(UserProfile,related_name='watching_lists')
    archived = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.id}->{self.name}->{self.board.id}->{self.board.name}"