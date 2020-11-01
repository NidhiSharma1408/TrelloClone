from django.contrib import admin
from . import models
# Register your models here.
admin.site.register(models.Team)
admin.site.register(models.Board)
admin.site.register(models.Preference)
admin.site.register(models.Card)
admin.site.register(models.Attached_file)
admin.site.register(models.Attached_link)
admin.site.register(models.List)
admin.site.register(models.Checklist)
admin.site.register(models.Task)