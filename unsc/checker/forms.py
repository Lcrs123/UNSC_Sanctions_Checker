from django import forms
from unsc.settings import DATABASES
import pandas as pd
from sqlalchemy import create_engine
from fuzzywuzzy import process


def get_match_results(self, chosen_list: str):
    # returns the match results with matching score added
    chosen_dataframe = self.list_choice_to_dataframe(chosen_list)
    match_results = process.extractBests(
        query=self.last_name_searched,
        choices=chosen_dataframe[
            'FULL_NAME' if chosen_list == 'Individuals' else 'FIRST_NAME'],
        score_cutoff=self.last_score_used,
        limit=None
    )
    match_lines = [x[-1] for x in match_results]
    df_matches = chosen_dataframe.iloc[match_lines].copy()
    df_matches.insert(loc=1, column='Score',
                      value=[x[-2] for x in match_results])
    return df_matches

class search_parameters(forms.Form):
    INDIVIDUALS = 'individuals'
    ENTITIES = 'entities'
    LIST_CHOICES = [
        (INDIVIDUALS,'Individuals List'),
        (ENTITIES,'Entities List')
    ]
    list_to_search = forms.ChoiceField(choices=LIST_CHOICES, initial='individuals')
    search_name = forms.CharField(help_text="Insert name to search for", max_length=512)
    matching_score = forms.IntegerField(initial=90, min_value=0,max_value=100)

    def get_search_results(self):
        engine = create_engine(f'sqlite:///{DATABASES["default"]["NAME"]}',
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






