from django import forms
from django.conf import settings
import pandas as pd
from sqlalchemy import create_engine
from fuzzywuzzy import process
from pydf import wkhtmltopdf
from os import path, rename
import pdfkit
from datetime import date
from django.template.loader import get_template

if path.exists(wkhtmltopdf.WK_PATH):
    rename(wkhtmltopdf.WK_PATH, path.join(path.dirname(wkhtmltopdf.WK_PATH),
                                 'wkhtmltopdf.exe'))

class search_parameters(forms.Form):
    INDIVIDUALS = 'individuals'
    ENTITIES = 'entities'
    LIST_CHOICES = [
        (INDIVIDUALS,'Individuals List'),
        (ENTITIES,'Entities List')
    ]
    WKHTMLTOPDF_PATH = path.join(path.dirname(wkhtmltopdf.WK_PATH),
                                 'wkhtmltopdf.exe')

    list_to_search = forms.ChoiceField(choices=LIST_CHOICES, initial='individuals')
    search_name = forms.CharField(help_text="Insert name to search for", max_length=512)
    matching_score = forms.IntegerField(initial=90, min_value=0,max_value=100)

    def get_search_results(self):
        engine = create_engine(f'sqlite:///{settings.DATABASES["default"]["NAME"]}',
                               echo=False)
        df = pd.read_sql(f'checker_{self["list_to_search"].value()}',
                         con=engine)
        match_results = process.extractBests(
        query=self['search_name'].value(),
        choices=df['FULL_NAME' if self["list_to_search"].value() == 'individuals' else 'FIRST_NAME'],
        score_cutoff=int(self['matching_score'].value()),
        limit=None
    )
        match_lines = [x[-1] for x in match_results]
        df_matches = df.iloc[match_lines].copy()
        df_matches.insert(loc=1, column='Score',
                          value=[x[-2] for x in match_results])
        return df_matches

    def generate_report(self, request_session):
        # Creates the report and returns the path to the file
        # The view function will delete the file once it's downloaded
        df_matches = self.get_search_results()
        df_html = df_matches.to_html(classes=['table', 'table-striped', 'table-dark', 'table-sm'],
                                     columns=df_matches.columns[:-1],
                                     index=False,
                                     )
        context = {
            'name_searched': f'{self["search_name"].value()}',
            'title': 'UNSC Sanctions list check',
            'score_used': self["matching_score"].value(),
            'num_matches': request_session['match_info']['num_matches'],
            'table': df_html,
            'date_of_search': str(date.today()),
            'list_searched': self['list_to_search'].value(),
            'list_date': request_session['list_date'],
            'form':request_session['last_form']
        }
        template = get_template('report.html')
        html_report = template.render(context)
        pdfkit_config = pdfkit.configuration(wkhtmltopdf=self.WKHTMLTOPDF_PATH)
        file_path = f'report_{self["search_name"].value()}_score_{self["matching_score"].value()}_matches_{request_session["match_info"]["num_matches"]}.pdf'
        pdfkit.from_string(html_report,output_path=file_path,configuration=pdfkit_config, css=path.join(settings.STATIC_CSS, 'bootstrap.css'), options={
            'enable-local-file-access': '',
            'page-size': 'A4',
            'margin-top': '0',
            'margin-right': '0',
            'margin-left': '0',
            'margin-bottom': '0',
            'zoom': '1',
            'encoding': "UTF-8",
        })
        return file_path





