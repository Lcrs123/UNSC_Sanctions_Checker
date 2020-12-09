from django.contrib import admin
from .models import ENTITIES,INDIVIDUALS

# Register your models here.

admin.site.register(INDIVIDUALS)
admin.site.register(ENTITIES)

# @admin.register(INDIVIDUALS)
# class IndividualAdmin(admin.ModelAdmin):
#     list_display = ('FULL_NAME',
#                     'DATAID',
#                     'VERSIONNUM',
#                     'UN_LIST_TYPE',
#                     'REFERENCE_NUMBER',
#                     'LISTED_ON',
#                     'COMMENTS1',
#                     'NAME_ORIGINAL_SCRIPT',
#                     'GENDER',
#                     'SUBMITTED_BY')
#
#
# @admin.register(ENTITIES)
# class EntitiesAdmin(admin.ModelAdmin):
#     list_display = ("FIRST_NAME",
#                     "DATAID",
#                     "VERSIONNUM",
#                     "UN_LIST_TYPE",
#                     "REFERENCE_NUMBER",
#                     "LISTED_ON",
#                     "COMMENTS1",
#                     "NAME_ORIGINAL_SCRIPT",
#                     "SUBMITTED_ON")

