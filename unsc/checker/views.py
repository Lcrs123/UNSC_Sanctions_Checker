from django.shortcuts import render
from .forms import search_parameters
from .models import INDIVIDUALS,ENTITIES
from django.http import HttpResponse
from os import remove, path
from datetime import date

def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_individuals = INDIVIDUALS.objects.count()
    num_entities = ENTITIES.objects.count()

    list_date = INDIVIDUALS.objects.values_list('LIST_DATE', flat=True)[0]
    is_index = True

    context = {
        'num_individuals': num_individuals,
        'num_entities': num_entities,
        'list_date': list_date,
        'is_index': is_index,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

def search(request):
    form = search_parameters(request.GET)
    form.full_clean()
    request.session['last_form'] = form.data
    list_is_entities = form['list_to_search'].value() == 'entities'
    list_date = INDIVIDUALS.objects.values_list('LIST_DATE', flat=True)[
        0].isoformat()
    df_matches = form.get_search_results()
    df_matches_json = df_matches.to_json()
    num_matches = len(df_matches)
    df_html = df_matches.to_html(classes=['table', 'table-striped', 'table-dark',
                        'table-responsive'], columns=df_matches.columns[:-1],
               index=False, justify='justify-all')
    request.session['match_info'] = {'df_matches_json':df_matches_json, 'num_matches':num_matches, 'df_html':df_html}
    request.session['list_date'] = list_date
    context = {
        'table':df_html,
        'num_matches':num_matches,
        'list_is_entities':list_is_entities,
        'form':request.session['last_form'],
        'list_date': list_date,
        'date_of_search': date.today()
    }
    return render(request, 'search.html', context=context)


def list(request, list_name:str=None):
    db_dict = {'individuals':INDIVIDUALS,'entities':ENTITIES}
    db = db_dict[list_name]()
    item_count = db_dict[list_name].objects.count()
    df_html = db.to_df_to_html()
    context = {
        'item_count': item_count,
        'table': df_html,
        'list_name': list_name.capitalize()
    }
    return render(request, 'list.html', context=context)


def save_report(request):
    form = search_parameters(request.session['last_form'])
    filename = form.generate_report(request_session=request.session)
    with open(filename,'rb') as file:
        filedata = file.read()
    response = HttpResponse(filedata, content_type='application/pdf')
    response['Content-Length'] = path.getsize(filename)
    response['Content-Disposition'] = 'attachment; filename=%s' % f'{filename}'
    remove(filename)
    return response




