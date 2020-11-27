from django.db import models
from django.core.validators import MaxValueValidator
from userauth.models import UserProfile
from teams.models import Team
import string,random
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify 
from django.db.models.signals import pre_save

class Board(models.Model):
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length = 250, null = True, blank = True)
    desc = models.TextField(blank=True,null=True,verbose_name="description")
    team = models.ForeignKey(Team,on_delete=models.SET_NULL,null=True,related_name='boards')
    members = models.ManyToManyField(UserProfile,related_name="member_in_boards")
    admins = models.ManyToManyField(UserProfile,related_name="admin_in_boards")
    starred_by = models.ManyToManyField(UserProfile,related_name="starred_boards")
    watched_by = models.ManyToManyField(UserProfile,related_name="watching_boards")
    is_closed = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.id} {self.name}"
    class Meta:
        ordering = ['team','-id']
        
class Preference(models.Model):
    class comments(models.IntegerChoices):
        disabled = 1,_("Disabled")
        admins = 2,_("Admins")
        members = 3,_("Admin and Board Members")
        team_members = 4,_("Admin, Board Members, Guests and team members")
        public = 5,_("anyone")
    class invitations(models.IntegerChoices):
        admins = 1,_('Only admins can add and remove members from this board')
        members =3,_('Only Members can add and remove members from this board')
    class permission(models.IntegerChoices):
        members = 3,_("Admin and Board Members")
        team_members = 4,_("Admin, Board Members, and team members")
        public = 5,_("anyone")
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



def random_string_generator(size = 10, chars = string.ascii_lowercase + string.digits): 
    return ''.join(random.choice(chars) for _ in range(size))  
def unique_slug_generator(instance, new_slug = None): 
    if new_slug is not None: 
        slug = new_slug 
    else: 
        slug = slugify(instance.name) 
    Klass = instance.__class__ 
    qs_exists = Klass.objects.filter(slug = slug).exists() 
    if qs_exists: 
        new_slug = "{slug}-{randstr}".format( 
            slug = slug, randstr = random_string_generator(size = 4)) 
        return unique_slug_generator(instance, new_slug = new_slug) 
    return slug 
def pre_save_receiver(sender, instance, *args, **kwargs): 
   if not instance.slug: 
       instance.slug = unique_slug_generator(instance) 
pre_save.connect(pre_save_receiver, sender =Board) 