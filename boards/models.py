from django.db import models
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
    guests = models.ManyToManyField(UserProfile,related_name="guest_in_boards")
    admins = models.ManyToManyField(UserProfile,related_name="admin_in_boards")
    starred_by = models.ManyToManyField(UserProfile,related_name="starred_boards")
    watched_by = models.ManyToManyField(UserProfile,related_name="watching_boards")
    is_closed = models.BooleanField(default=False)
    personal = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.id} {self.name}"

class Preference(models.Model):
    class comments(models.IntegerChoices):
        disabled = 0,_("Disabled")
        org = 1,_("Team Members and Guest Members")
        members = 2,_("Only team or members associated with object(card/list/board)")
        observers = 3,_("Only observers")
        public = 4,_("Public")
    class invitations(models.IntegerChoices):
        admins = 0,_('Only admins can send invitation')
        members =1,_('Only Members can send invitation')
    class permission(models.IntegerChoices):
        org = 0,_("Team Members and Guest Members")
        private = 1,_("Only admins and members")
        public = 2,_("Public")
    class voting(models.IntegerChoices):
        disabled = 0,_("Disabled")
        org = 1,_("Team Members and Guest Members")
        members = 2,_("Only team or members associated with object(card/list/board)")
        observers = 3,_("Only observers")
        public = 4,_("Public")
    self_join = models.BooleanField(default=True)
    card_cover = models.BooleanField(default=True)
    # background = models.OneToOneField(Background,on_delete=models.SET_NULL,null=True,related_name="pref_object")
    pref_comment = models.IntegerField(choices=comments.choices,default=comments.disabled)
    pref_invitation = models.IntegerField(choices=invitations.choices,default=invitations.members)
    permission_level = models.IntegerField(choices=permission.choices,default=permission.org)
    pref_voting = models.IntegerField(choices=voting.choices,default=voting.disabled)
    board = models.OneToOneField(Board,on_delete=models.CASCADE,related_name="preference")
    def __str__(self):
        return f"{self.board.id}->{self.board.name}"


