from django.shortcuts import render
# from django.views import generic
from .forms import search_parameters
from .models import INDIVIDUALS,ENTITIES


def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_individuals = INDIVIDUALS.objects.count()
    num_entities = ENTITIES.objects.count()

    list_date = INDIVIDUALS.objects.values_list('LIST_DATE', flat=True)[0].isoformat()

    context = {
        'num_individuals': num_individuals,
        'num_entities': num_entities,
        'list_date': list_date
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

def search(request):
    form = search_parameters(request.GET)
    df_matches = form.get_search_results()
    num_matches = len(df_matches)
    name_searched = form['search_name'].value()
    chosen_list = form['list_to_search'].value().capitalize()
    score_used = form['matching_score'].value()
    df_html = df_matches.to_html(classes=['table', 'table-striped', 'table-dark',
                        'table-responsive'], columns=df_matches.columns[:-1],
               index=False, justify='justify-all')
    context = {
        'table':df_html,
        'num_matches':num_matches,
        'name_searched':name_searched,
        'chosen_list':chosen_list,
        'score_used':score_used
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

# class IndividualsListView(generic.ListView):
#     model = INDIVIDUALS
#
# class IndividualDetailView(generic.DetailView):
#     model = INDIVIDUALS
#
# class EntitiesListView(generic.ListView):
#     model = ENTITIES
#
# class EntityDetailView(generic.DetailView):
#     model = ENTITIES