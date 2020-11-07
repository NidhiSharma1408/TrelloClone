from django.db import models
from django.core.validators import MaxValueValidator
from django.utils.translation import gettext_lazy as _
from userauth.models import UserProfile


class Team(models.Model):
    class Type(models.TextChoices):
        HumanResource = 'HR', _('Human Resorce')
        Marketing = 'MT', _('Marketing')
        Operations = 'OP', _('Operations')
        Sales_CRM = 'SR', _('Sales CRM')
        Education = 'ED', _('Education')
        Small_Business = 'SB', _('Small Business')
        Engineering_IT = 'EI', _('Engineering-IT')
        Other = 'OT', _('Other')
    Type_of_team = models.CharField(
        max_length=2,
        choices=Type.choices,
        default=Type.Other,
    )
    desc = models.TextField(blank=True,null=True,verbose_name="description")
    name = models.CharField(blank=False,max_length=50)
    members = models.ManyToManyField(UserProfile,related_name="teams")
    website = models.URLField(null=True,blank=True)
    is_private = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.id}-{self.name}"
    

class Board(models.Model):
    name = models.CharField(max_length=50)
    desc = models.TextField(blank=True,null=True,verbose_name="description")
    team = models.ForeignKey(Team,on_delete=models.SET_NULL,null=True,related_name='boards')
    members = models.ManyToManyField(UserProfile,related_name="member_in_boards")
    admins = models.ManyToManyField(UserProfile,related_name="admin_in_boards")
    starred_by = models.ManyToManyField(UserProfile,related_name="starred_boards")
    watched_by = models.ManyToManyField(UserProfile,related_name="watching_boards")
    is_closed = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.id} {self.name}"

class Preference(models.Model):
    class comments(models.IntegerChoices):
        disabled = 1,_("Disabled")
        admins = 2,_("Admins")
        members = 3,_("Admin and Board Members")
        team_members = 4,_("Admin, Board Members, Guests and team members")
        public = 5,_("anyone")
    class invitations(models.IntegerChoices):
        admins = 0,_('Only admins can add and remove members from this board')
        members =1,_('Only Members can add and remove members from this board')
    class permission(models.IntegerChoices):
        admins = 1,_("Admins")
        members = 2,_("Admin and Board Members")
        team_members = 3,_("Admin, Board Members, and team members")
        public = 4,_("anyone")
    class voting(models.IntegerChoices):
        disabled = 1,_("Disabled")
        admins = 2,_("Admins")
        members = 3,_("Admin and Board Members")
        team_members = 4,_("Admin, Board Members, Guests and team members")
        public = 5,_("anyone")
    self_join = models.BooleanField(default=True)
    card_cover = models.BooleanField(default=False)
    pref_comment = models.IntegerField(choices=comments.choices,default=comments.disabled)
    pref_invitation = models.IntegerField(choices=invitations.choices,default=invitations.members)
    permission_level = models.IntegerField(choices=permission.choices,default=permission.team_members)
    pref_voting = models.IntegerField(choices=voting.choices,default=voting.disabled)
    board = models.OneToOneField(Board,on_delete=models.CASCADE,related_name="preference")
    voting_visible = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.board.id}->{self.board.name}"

class List(models.Model):
    board = models.ForeignKey(Board,on_delete=models.CASCADE,related_name='lists')
    name = models.CharField(max_length=30)
    watched_by = models.ManyToManyField(UserProfile,related_name='lists_watching')
    archived = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.id}->{self.name}->{self.board.id}->{self.board.name}"

class Card(models.Model):
    name = models.CharField(max_length=50)
    desc = models.TextField(blank=True,null=True)
    priority = models.PositiveIntegerField(default=1,validators=[MaxValueValidator(10)])
    members = models.ManyToManyField(UserProfile,related_name='member_in_card')
    due_date = models.DateTimeField(null=True)
    complete = models.BooleanField(default=False)
    list = models.ForeignKey(List,on_delete=models.CASCADE,related_name='cards')
    archived = models.BooleanField(default=False)
    watched_by = models.ManyToManyField(UserProfile,related_name='watching_cards')
    voted_by = models.ManyToManyField(UserProfile,related_name='voted_cards')
    def __str__(self):
        return f'{self.id}-{self.name}-{self.list.id}-{self.list.board.id}'
    class Meta:
        ordering = ['-priority']


class Attached_file(models.Model):
    card = models.ForeignKey(Card,on_delete=models.CASCADE,related_name='attached_files')
    file = models.FileField(null=False)

class Attached_link(models.Model):
    card = models.ForeignKey(Card,on_delete=models.CASCADE,related_name='attached_links')
    link = models.URLField(blank=False,null=False)

class Checklist(models.Model):
    card = models.ForeignKey(Card,on_delete=models.CASCADE,related_name='checklists')
    name = models.CharField(default='Checklist',max_length=50)

class Task(models.Model):
    checklist = models.ForeignKey(Checklist,on_delete=models.CASCADE,related_name='tasks')
    name = models.CharField(max_length=50,null=False)
    completed = models.BooleanField(default=False)

class Comment(models.Model):
    card = models.ForeignKey(Card,on_delete=models.CASCADE,related_name='comments')
    text = models.TextField(blank=False)
    user = models.ForeignKey(UserProfile,on_delete=models.CASCADE,related_name='comments')
    created_at = models.DateTimeField(auto_now=True)

class Label(models.Model):
    color = models.CharField(max_length=6)
    name = models.CharField(max_length=30)
    card = models.ForeignKey(Card,on_delete=models.CASCADE,related_name='label')

class Activity(models.Model):
    description = models.TextField()
    time_created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(UserProfile,on_delete=models.DO_NOTHING,related_name='activity')

