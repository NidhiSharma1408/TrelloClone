from django.contrib import admin
from . import models
# Register your models here.
admin.site.register(models.Card)
admin.site.register(models.Comment)
admin.site.register(models.Label)
admin.site.register(models.Attached_file)
admin.site.register(models.Attached_link)