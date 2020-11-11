import pandas as pd
import xml.etree.ElementTree as et
from fuzzywuzzy import process
from tkinter import *
from tkinter import filedialog,ttk
from os import getcwd
import requests

def get_column_list(element) -> list:
    assert element.tag in ['INDIVIDUALS','ENTITIES'], f'Element parameter tag must be either "INDIVIDUALS" or "ENTITIES". Provided was {element.tag}'
    element_columns = []
    first_child = list(list(element)[0])
    for column in first_child:
        element_columns.append(column.tag)
    return element_columns

def append_individuals_full_names(df):
    df = df.fillna(value={'FIRST_NAME': ' ', 'SECOND_NAME': ' ','THIRD_NAME': ' '})
    df[['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME']] = df[['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME']].astype(str)
    df['FULL_NAME'] = df['FIRST_NAME'] + df['SECOND_NAME'] + df['THIRD_NAME']
    return df

class Application():
    def __init__(self):
        self.list = None
        self.elements_list = []
        self.individuals_df = None
        self.entities_df = None

    def load_list(self):
        path_window = Tk()
        xml_list_path = filedialog.askopenfilename(initialdir=getcwd(), filetypes=[('Xml files','*.xml')], title='Choose xml list')
        path_window.withdraw()
        path_window.destroy()
        self.list = et.parse(xml_list_path)
        root = self.list.getroot()
        self.elements_list.extend(list(root)[0:2])

    def make_element_dfs(self):
        for element in self.elements_list:
            assert element.tag in ['INDIVIDUALS','ENTITIES'], f'Element parameter tag must be either "INDIVIDUALS" or "ENTITIES". Provided was {element.tag}'
            df = pd.DataFrame(columns=get_column_list(element))
            for child in list(element):
                child_dict = {}
                for column in list(child):
                    child_dict[column.tag] = column.text
                df = df.append(child_dict, ignore_index=True)
            if element.tag == 'INDIVIDUALS':
                self.individuals_df = df
            elif element.tag == 'ENTITIES':
                self.entities_df = df

    def clean_individuals_df(self):
        self.individuals_df.fillna(value={'FIRST_NAME': '', 'SECOND_NAME': '', 'THIRD_NAME': '','FOURTH_NAME': ''}, inplace=True)
        self.individuals_df[['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME', 'FOURTH_NAME']] = self.individuals_df[['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME', 'FOURTH_NAME']].astype(str)

    def append_individuals_full_name(self):
        self.individuals_df['FULL_NAME'] = self.individuals_df[['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME', 'FOURTH_NAME']].apply(lambda x: ' '.join(x),axis=1)
        self.individuals_df['FULL_NAME'] = self.individuals_df['FULL_NAME'].str.strip()
        while self.individuals_df['FULL_NAME'].str.contains('  ').any():
            self.individuals_df['FULL_NAME'] = self.individuals_df['FULL_NAME'].str.replace('  ', ' ')

    def load_button(self):
        self.load_list()
        self.make_element_dfs()
        self.clean_individuals_df()
        self.append_individuals_full_name()

def search_button():
    name = str(name_entry.get())
    matches.set(str(process.extractBests(query=name, choices=app.individuals_df['FULL_NAME'],score_cutoff=score.get())).replace(',','\n'))


if __name__ == '__main__':
    app = Application()
    root = Tk()
    root.title('UNSC Sanctions Checker')

    mainframe = ttk.Frame(root, padding = '4 4 20 20')
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    ttk.Button(mainframe, text='Load list', command=app.load_button).grid(column=0,row=0, sticky=(N, W))

    name = StringVar()
    name_entry = ttk.Entry(mainframe, width=24, textvariable=name)
    name_entry.grid(column=2, row=1, sticky=(W, E))
    ttk.Label(mainframe, text='Name:').grid(column=2,row=0, sticky=W)

    score = IntVar(value=100)
    score_entry = ttk.Entry(mainframe, width=3,textvariable=score)
    score_entry.grid(column=4, row=1)
    ttk.Label(mainframe, text='Score').grid(column=3,row=1)

    ttk.Button(mainframe, text='Search name', command=search_button).grid(column=2,row=2, sticky=(N, W))

    matches = StringVar()
    ttk.Label(mainframe, textvariable=matches).grid(column=1, row=4, sticky=S)
    ttk.Label(mainframe, text='Matches:').grid(column=1,row=3,sticky=W)



    name_entry.focus()

    root.mainloop()