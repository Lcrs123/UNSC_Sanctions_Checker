import xml.etree.ElementTree as et
from os import getcwd, listdir, stat
from tkinter import *
from tkinter import filedialog, ttk, messagebox, simpledialog

import pandas as pd
import requests
from fuzzywuzzy import process


def get_column_list(element) -> list:
    assert element.tag in ['INDIVIDUALS','ENTITIES'], f'Element parameter tag must be either "INDIVIDUALS" or "ENTITIES". Provided was {element.tag}'
    element_columns = []
    first_child = list(list(element)[0])
    for column in first_child:
        element_columns.append(column.tag)
    return element_columns


class Application(object):

    loading_warning = 'Loading list, please wait.'

    UNSC_sanctions_list_url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"

    def __init__(self):
        self.list = None
        self.elements_list = []
        self.individuals_df = None
        self.entities_df = None
        self.root = Tk()
        self.list_path = 'consolidated.xml'
        self.list_downloaded = False
        self.list_loaded = False
        self.list_info = StringVar(value='List not loaded.')

    def create_frame(self):
        self.mainframe = ttk.Frame(self.root, padding='4 4 20 20')
        self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def create_load_button(self):
        ttk.Button(self.mainframe, text='Load list', command=self.load_button).grid(
            column=0, row=0, sticky=W)

    def create_list_info(self):
        ttk.Label(self.mainframe, textvariable=self.list_info).grid(column=0,row=3,rowspan=3)

    def create_get_list_button(self):
        ttk.Button(self.mainframe, text="Get list online", command=self.get_list_button).grid(column=0,row=1, sticky=W)

    def create_check_update_button(self):
        ttk.Button(self.mainframe, text="Check for update",
                   command=self.check_update_button).grid(column=0, row=2, sticky=W)

    def create_name_entry(self):
        self.name = StringVar()
        self.name_entry = ttk.Entry(self.mainframe, width=24,
                                    textvariable=self.name)
        self.name_entry.grid(column=2, row=0, sticky=W)
        ttk.Label(self.mainframe, text='Name:').grid(column=1, row=0, sticky=E)

    def create_score_entry(self):
        self.score = IntVar(value=100)
        self.score_entry = ttk.LabeledScale(self.mainframe,
                                            variable=self.score, from_=100,
                                            to=0)
        self.score_entry.grid(column=2, row=1)
        self.score_entry.label.update()
        ttk.Label(self.mainframe, text='Minimum Score Match:').grid(column=1,
                                                                    row=1)

    def create_search_button(self):
        ttk.Button(self.mainframe, text='Search name',
                   command=self.search_button).grid(column=3, row=0, sticky=W)

    def create_matches_list(self):
        self.matches = StringVar()
        ttk.Label(self.mainframe, text='Matches:').grid(column=1, row=3,
                                                        sticky=W)
        ttk.Label(self.mainframe, textvariable=self.matches).grid(column=1,
                                                                  row=4,
                                                                  columnspan=9)

    def search_button(self):
        if self.check_is_list_loaded():
            name = str(self.name_entry.get())
            self.matches.set(process.extractBests(query=name,
                                                      choices=
                                                      self.individuals_df[
                                                          'FULL_NAME'],
                                                      score_cutoff=self.score.get()))

    def connect_to_link(self, url=UNSC_sanctions_list_url):
        r = requests.get(url)
        if r.status_code == 200 and r.headers['Content-Type'].__contains__(
            'xml') and r.text.__contains__('CONSOLIDATED_LIST'):
            return r
        else:
            if messagebox.askyesno(message=(
            f'Could not find the list at {url}\nWould you like to try with a different link?')):
                return self.connect_to_link(
                    url=simpledialog.askstring(title='Insert new link',
                                               prompt=f'Please enter new adress for UNSC Sanctions list in xml format\nLast address used:{url}'))

    def check_list_is_outdated(self,requests_object):
        if int(requests_object.headers['Content-Length']) == stat(path=self.list_path)[-4]:
            return False
        else:
            return True

    def check_update_button(self):
        try:
            r = self.connect_to_link()
            if self.check_list_is_outdated(r):
                if messagebox.askyesno(message='Current list is outdated, download new one?'):
                    self.get_list_button()
            else:
                messagebox.showinfo(message=f"List is up-to-date.\nList on UNSC site has {r.headers['Content-Length']} bytes.\nLoaded list has {stat(path=self.list_path)[-4]} bytes." )
        except AttributeError:
            messagebox.showerror(message='Could not download list. Try again with a different link or choose it manually')

    def save_downloaded_list(self, requests_object):
        try:
            savepath = filedialog.asksaveasfilename(initialdir=getcwd(),initialfile='consolidated.xml', filetypes= [('Xml files','*.xml')])
            with open(savepath, 'wb') as fd:
                for chunk in requests_object.iter_content(chunk_size=128):
                    fd.write(chunk)
                messagebox.showinfo(message=f'List downloaded from {requests_object.url} and saved as {savepath} at {getcwd()}')
            self.list_path = savepath
            self.list_downloaded = True
        except AttributeError:
            messagebox.showerror(message='Could not download list. Try again with a different link or choose it manually')

    def get_list_button(self):
        if self.list_loaded:
            if messagebox.askyesno(message='A list is already loaded. Would you like to download it again?'):
                r = self.connect_to_link()
                self.save_downloaded_list(r)
                if messagebox.askyesno(message='Would you like to load the downloaded list now?\nYou have the option to manually load it later.'):
                    self.autoload_list()
        else:
            r = self.connect_to_link()
            self.save_downloaded_list(r)
            if messagebox.askyesno(
                    message='Would you like to load the downloaded list now?\nYou have the option to manually load it later.'):
                self.autoload_list()

    def check_for_list(self):
        if "consolidated.xml" in listdir(getcwd()) or self.list_downloaded:
            return True
        else:
            return False

    def autoload_list(self):
        try:
            if self.check_for_list():
                print(Application.loading_warning)
                self.list = et.parse(self.list_path)
                root = self.list.getroot()
                self.elements_list.extend(list(root)[0:2])
                self.make_element_dfs()
                self.clean_individuals_df()
                self.append_individuals_full_name()
                messagebox.showinfo(message=f"Loaded list from file 'consolidated.xml' in dir {getcwd()}")
                self.update_list_info()
            else:
                messagebox.showinfo(message="Could not find list file ('consolidated.xml') in current dir\nPlease load the list manually or get it from the UNSC website")
        except:
            messagebox.showinfo(
                message=f"Could not load file {self.list_path} in current dir\nPlease load the list manually or get it from the UNSC website")

    def update_list_info(self):
        self.list_loaded = True
        self.list_info.set(value=f'List loaded.\nNumber of Individuals: {self.individuals_df.__len__()}\nNumber of Entities: {self.entities_df.__len__()}')

    def load_list(self):
        path_window = Tk()
        self.list_path = filedialog.askopenfilename(initialdir=getcwd(), filetypes=[('Xml files','*.xml')], title='Choose xml list')
        path_window.withdraw()
        path_window.destroy()
        self.list = et.parse(self.list_path)
        etree_root = self.list.getroot()
        self.elements_list.extend(list(etree_root)[0:2])

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
        print(Application.loading_warning)
        self.make_element_dfs()
        self.clean_individuals_df()
        self.append_individuals_full_name()
        self.update_list_info()

    def check_is_list_loaded(self):
        if self.list_loaded:
            return True
        else:
            messagebox.showerror(message='Sanctions list not loaded.')
            return False

    def main(self):
        self.root.title('UNSC Sanctions Checker')
        self.create_frame()
        self.create_load_button()
        self.create_name_entry()
        self.create_search_button()
        self.create_matches_list()
        self.create_get_list_button()
        self.create_check_update_button()
        self.create_score_entry()
        self.create_list_info()
        self.autoload_list()
        self.name_entry.focus_force()
        self.root.mainloop()


if __name__ == '__main__':
    app = Application()
    app.main()