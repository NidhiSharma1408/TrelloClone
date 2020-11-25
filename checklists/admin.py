from django.contrib import admin
from . import models
# Register your models here.
admin.site.register(models.Checklist)
admin.site.register(models.Task)