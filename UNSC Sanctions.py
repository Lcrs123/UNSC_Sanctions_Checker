import pandas as pd
import xml.etree.ElementTree as et
from fuzzywuzzy import process
from tkinter import *
from tkinter import filedialog,ttk, messagebox,simpledialog
from os import getcwd, listdir, stat
import requests

def get_column_list(element) -> list:
    assert element.tag in ['INDIVIDUALS','ENTITIES'], f'Element parameter tag must be either "INDIVIDUALS" or "ENTITIES". Provided was {element.tag}'
    element_columns = []
    first_child = list(list(element)[0])
    for column in first_child:
        element_columns.append(column.tag)
    return element_columns

class Application():
    def __init__(self):
        self.list = None
        self.list_found = False
        self.elements_list = []
        self.individuals_df = None
        self.entities_df = None
        self.root = Tk()
        self.list_path = 'consolidated.xml'

    def create_frame(self):
        self.mainframe = ttk.Frame(self.root, padding='4 4 20 20')
        self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def create_load_button(self):
        ttk.Button(self.mainframe, text='Load list', command=self.load_button).grid(
            column=0, row=0, sticky=(N, W))

    def create_get_list_button(self):
        ttk.Button(self.mainframe, text="Get list online", command=self.get_list_button).grid(column=1,row=0)

    def connect_to_link(self,link="https://scsanctions.un.org/resources/xml/en/consolidated.xml"):
        r = requests.get(link)
        if r.status_code == 200 and r.headers['Content-Type'].__contains__(
            'xml') and r.text.__contains__('CONSOLIDATED_LIST'):
            return r
        else:
            if messagebox.askyesno(message=(
            f'Could not find the list at {link}\nWould you like to try with a different link?')):
                self.connect_to_link(link=simpledialog.askstring(
                    prompt=f'Please enter new adress for UNSC Sanctions list in xml format\n Last address used:{link}'))

    def create_check_update_button(self):
        ttk.Button(self.mainframe, text="Check for update",
                   command=self.check_update_button).grid(column=2, row=0)

    def check_list_is_outdated(self,requests_object):
        if int(requests_object.headers['Content-Length']) == stat(path=self.list_path)[-4]:
            return False
        else:
            return True

    def check_update_button(self):
        r = self.connect_to_link()
        if self.check_list_is_outdated(r):
            if messagebox.askyesno(message='Current list is outdated, download new one?'):
                self.get_list_button()
        else:
            messagebox.showinfo(message='List is up-to-date')


    def save_downloaded_list(self, requests_object):
        with open('consolidated.xml', 'wb') as fd:
            for chunk in requests_object.iter_content(chunk_size=128):
                fd.write(chunk)
        messagebox.showinfo(message=f'List downloaded from {requests_object.url} and saved as consolidated.xml at {getcwd()}')


    def get_list_button(self):
        r = self.connect_to_link()
        self.save_downloaded_list(r)
        self.autoload_list()

    def create_name_entry(self):
        self.name = StringVar()
        self.name_entry = ttk.Entry(self.mainframe, width=24, textvariable=self.name)
        self.name_entry.grid(column=2, row=1, sticky=(W, E))
        ttk.Label(self.mainframe, text='Name:').grid(column=2, row=0, sticky=W)

    def create_score_entry(self):
        self.score = IntVar(value=100)
        self.score_entry = ttk.Entry(self.mainframe, width=3,textvariable=self.score)
        self.score_entry.grid(column=4, row=1)
        ttk.Label(self.mainframe, text='Score').grid(column=3,row=1)

    def create_search_button(self):
        ttk.Button(self.mainframe, text='Search name', command=self.search_button).grid(column=2,row=2, sticky=(N, W))

    def create_matches_list(self):
        self.matches = StringVar()
        ttk.Label(self.mainframe, text='Matches:').grid(column=1, row=3,
                                                        sticky=W)
        ttk.Label(self.mainframe, textvariable=self.matches).grid(column=1, row=4,
                                                        sticky=S)

    def check_for_list(self):
        if "consolidated.xml" in listdir(getcwd()):
            return True
        else:
            return False

    def autoload_list(self):
        if self.check_for_list():
            self.list = et.parse("consolidated.xml")
            root = self.list.getroot()
            self.elements_list.extend(list(root)[0:2])
            self.make_element_dfs()
            self.clean_individuals_df()
            self.append_individuals_full_name()
            messagebox.showinfo(message=f"Loaded list from file 'consolidated.xml' in dir {getcwd()}")
        else:
            messagebox.showinfo(message="Could not find list file ('consolidated.xml') in current dir\nPlease load the list manually or get it from the UNSC website")

    def load_list(self):
        path_window = Tk()
        self.list_path = filedialog.askopenfilename(initialdir=getcwd(), filetypes=[('Xml files','*.xml')], title='Choose xml list')
        path_window.withdraw()
        path_window.destroy()
        self.list = et.parse(self.list_path)
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

    def search_button(self):
        name = str(self.name_entry.get())
        self.matches.set(str(process.extractBests(query=name,
                                             choices=self.individuals_df[
                                                 'FULL_NAME'],
                                             score_cutoff=self.score.get())).replace(
            ',', '\n'))

    def main(self):
        self.root.title('UNSC Sanctions Checker')
        self.create_frame()
        self.create_load_button()
        self.create_name_entry()
        self.create_score_entry()
        self.create_search_button()
        self.create_matches_list()
        self.create_get_list_button()
        self.create_check_update_button()
        self.autoload_list()
        self.root.mainloop()



if __name__ == '__main__':
    app = Application()
    app.main()

