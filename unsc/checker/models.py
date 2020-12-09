from django.db import models
from django.urls import reverse
import pandas as pd
from sqlalchemy import create_engine
from django.conf import settings

# Create your models here.

class shared_methods:
    def to_df_to_html(self):
        engine = create_engine(f'sqlite:///{settings.DATABASES["default"]["NAME"]}',
                               echo=False)
        df = pd.read_sql(f'checker_{str(self.__class__.__name__).lower()}',
                         con=engine)
        df_html = df.to_html(classes=['table', 'table-striped', 'table-dark', 'table-responsive'], columns=df.columns[:-1],index=False, justify='justify-all')
        return df_html

class INDIVIDUALS(models.Model, shared_methods):

    FULL_NAME = models.CharField(max_length=511)
    DATAID = models.CharField(primary_key=True,max_length=512)
    VERSIONNUM = models.IntegerField()
    UN_LIST_TYPE = models.CharField(max_length=512)
    REFERENCE_NUMBER = models.CharField(max_length=512)
    LISTED_ON = models.DateField()
    COMMENTS1 = models.TextField()
    NAME_ORIGINAL_SCRIPT = models.CharField(max_length=512)
    GENDER = models.CharField(max_length=512)
    SUBMITTED_BY = models.CharField(max_length=512)
    LIST_DATE = models.DateField(default='1900-01-01')

    def get_absolute_url(self):
        return reverse('individual-detail', args=[str(self.DATAID)])

    def __str__(self):
        return self.FULL_NAME

    def get_fields_and_values(self):
        return [(field, field.value_to_string(self)) for field in INDIVIDUALS._meta.fields]


class ENTITIES(models.Model, shared_methods):

    FIRST_NAME = models.CharField(max_length=512)
    DATAID = models.CharField(primary_key=True, max_length=512)
    VERSIONNUM = models.IntegerField()
    UN_LIST_TYPE = models.CharField(max_length=512)
    REFERENCE_NUMBER = models.CharField(max_length=512)
    LISTED_ON = models.DateField()
    COMMENTS1 = models.TextField(null=True,blank=True)
    NAME_ORIGINAL_SCRIPT = models.CharField(max_length=512, null=True,blank=True)
    SUBMITTED_ON = models.CharField(max_length=512, null=True,blank=True)
    LIST_DATE = models.DateField(default='1900-01-01')

    def __str__(self):
        return self.FIRST_NAME

    def get_absolute_url(self):
        return reverse('entity-detail', args=[str(self.DATAID)])

    def get_fields_and_values(self):
        return [(field, field.value_to_string(self)) for field in
                ENTITIES._meta.fields]

