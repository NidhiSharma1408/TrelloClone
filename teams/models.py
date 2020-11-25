from django.db import models
from django.utils.translation import gettext_lazy as _
from userauth.models import UserProfile
# Create your models here.

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
    
