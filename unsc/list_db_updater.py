import os
import requests
import xml.etree.ElementTree as et
import pandas as pd
from datetime import date
from sqlalchemy import create_engine
if __name__ == '__main__':
    from unsc.settings import DATABASES
else:
    from unsc.unsc.settings import DATABASES

UNSC_sanctions_list_url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"


def connect_to_url(url:str=UNSC_sanctions_list_url) -> requests.Request:
    r = requests.get(url)
    if r.status_code == 200 and r.headers['Content-Type'].__contains__(
            'xml') and r.text.__contains__('CONSOLIDATED_LIST'):
        return r
    else:
        raise ConnectionError(f'Could not read list from url {url}')


def read_xml(requests_object: requests.Request) -> et.ElementTree:
    with open(file='list.xml',mode='wb') as file:
        for chunk in requests_object.iter_content(chunk_size=128):
            file.write(chunk)
    element_tree = et.parse(file.name)
    if os.path.exists(file.name):
        os.remove(file.name)
    return element_tree

def element_tree_to_list(element_tree: et.ElementTree) -> list:
    root = element_tree.getroot()
    elements_list = list(root)[0:2]
    return elements_list

def get_list_date(element_tree: et.ElementTree) -> date:
    root = element_tree.getroot()
    date_str = root.items()[1][1]
    iso_date = date.fromisoformat(date_str[:10])
    return iso_date

def get_column_list(element:list) -> list:
    assert element.tag in ['INDIVIDUALS',
                           'ENTITIES'], f'Element parameter tag must be either "INDIVIDUALS" or "ENTITIES". Provided was {element.tag}'
    element_columns = []
    first_child = list(list(element)[0])
    for column in first_child:
        element_columns.append(column.tag)
    return element_columns

def elements_list_to_df(elements_list:list) -> dict:
    df_dict = {}
    for element in elements_list:
        assert element.tag in ['INDIVIDUALS',
                               'ENTITIES'], f'Element parameter tag must be either "INDIVIDUALS" or "ENTITIES". Provided was {element.tag}'
        df = pd.DataFrame(columns=get_column_list(element))
        for child in list(element):
            child_dict = {}
            for column in list(child):
                child_dict[column.tag] = column.text
            df = df.append(child_dict, ignore_index=True)
        df_dict[element.tag] = df
    return df_dict

def clean_individuals_df(dataframe: pd.DataFrame) -> pd.DataFrame:
    # Fills name columns NAs with empty strings, turns name columns dtype
    # to str, drops columns with all NAs.
    dataframe.fillna(
        value={'FIRST_NAME': '', 'SECOND_NAME': '', 'THIRD_NAME': '',
               'FOURTH_NAME': ''}, inplace=True)
    dataframe[
        ['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME', 'FOURTH_NAME']] = \
        dataframe[
            ['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME',
             'FOURTH_NAME']].astype(
            str)
    dataframe.loc[:,'LISTED_ON'] = dataframe['LISTED_ON'].astype(
        dtype='datetime64').dt.date
    dataframe = dataframe.dropna(axis=1, how='all')
    return dataframe


def clean_entities_df(dataframe: pd.DataFrame) -> pd.DataFrame:
    # drop columns with all NAs, put FIRST_NAME column first, change listed
    # on dtype
    dataframe.loc[:,'LISTED_ON'] = dataframe['LISTED_ON'].astype(
        dtype='datetime64').dt.date
    dataframe = dataframe[
        ['FIRST_NAME'] + [col for col in dataframe.columns if
                          col != 'FIRST_NAME']]
    dataframe = dataframe.dropna(axis=1, how='all')
    return dataframe


def append_individuals_full_name(dataframe: pd.DataFrame) -> pd.DataFrame:
    # Creates a full name column for every individual on list, drops used
    # name columns. Full name column is the one used for matching.
    dataframe['FULL_NAME'] = dataframe[
        ['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME', 'FOURTH_NAME']].apply(
        lambda x: ' '.join(x), axis=1)
    dataframe['FULL_NAME'] = dataframe[
        'FULL_NAME'].str.strip()
    while dataframe['FULL_NAME'].str.contains('  ').any():
        dataframe['FULL_NAME'] = dataframe[
            'FULL_NAME'].str.replace('  ', ' ')
    dataframe = dataframe.drop(
        labels=['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME', 'FOURTH_NAME'],
        axis=1)
    dataframe = dataframe[
        ['FULL_NAME'] + [col for col in dataframe.columns if
                         col != 'FULL_NAME']]
    return dataframe

def clean_dfs(df_dict:dict, list_date:date) -> dict:
    df_dict['INDIVIDUALS'] = clean_individuals_df(df_dict['INDIVIDUALS'])
    df_dict['INDIVIDUALS'] = append_individuals_full_name(df_dict['INDIVIDUALS'])
    df_dict['ENTITIES'] = clean_entities_df(df_dict['ENTITIES'])
    for key in df_dict:
        df_dict[key]['LIST_DATE'] = list_date.isoformat()
    return df_dict

def connect_to_db(db_address:str):
    engine = create_engine(db_address, echo=False)
    engine._db_adress = db_address
    if len(engine.table_names()) == 0:
        raise ConnectionError(f'Connection to address {db_address} returned a DB with 0 tables. Check if address is correct.')
    return engine


def df_to_db(dataframe:pd.DataFrame, app_name:str, table_name:str, connection_engine,list_date:date,mode:str='replace') -> None:
    current_db_list_date = connection_engine.execute(f'SELECT LIST_DATE FROM {app_name}_{table_name.lower()}').fetchone()
    if current_db_list_date[0] == list_date.isoformat():
        print(f'Loaded list for {table_name} on table {app_name}_{table_name.lower()} is already up-to-date, table not changed.')
    else:
        dataframe.to_sql(f'{app_name}_{table_name.lower()}', con=connection_engine, if_exists=mode, index=False)
        print(f'Sucessfully updated table {app_name}_{table_name.lower()}')


def main(db_adress=f'sqlite:///{DATABASES["default"]["NAME"]}'):
    target_app_name = 'checker'
    print(f'Starting script at directory {os.getcwd()}')
    r = connect_to_url()
    print(f'Successfully connected and downloaded list from {r.url}')
    elements_tree = read_xml(r)
    print(f'Successfully read xml list')
    list_date = get_list_date(elements_tree)
    print(f'Successfully got list date: {list_date.isoformat()}')
    elements_list = element_tree_to_list(elements_tree)
    print(f'Successfully turned element tree to element list')
    df_dict = elements_list_to_df(elements_list)
    print(f'Successfully turned element list to dataframes dictionary')
    cleaned_df_dict = clean_dfs(df_dict,list_date)
    print(f'Successfully cleaned dataframes in dictionary')
    engine = connect_to_db(db_address=db_adress)
    print(f'Successfully created SQL engine connection with database at {engine._db_adress}')
    print(f'Available tables for app {target_app_name}: {[table for table in engine.table_names() if target_app_name in table]}')
    for key,value in cleaned_df_dict.items():
        df_to_db(dataframe=value, app_name=target_app_name,table_name=key, connection_engine=engine, list_date=list_date)

if __name__ == '__main__':
    main()







