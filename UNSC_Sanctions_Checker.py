import xml.etree.ElementTree as et
from datetime import date
from os import getcwd, listdir, stat
from tkinter import *
from tkinter import filedialog, ttk, messagebox, simpledialog

import pandas as pd
import pdfkit
import requests
from fuzzywuzzy import process
from jinja2 import Environment, FileSystemLoader


def interface_method(f):
    # Decorator for identifying interface methods for easier calling
    f._is_interface_method = True
    return f


class Application(object):
    loading_warning = 'Loading list, please wait.'
    UNSC_sanctions_list_url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"

    @staticmethod
    def get_column_list(element) -> list:
        # takes a xml element tree and returns the childrens names as a column list
        assert element.tag in ['INDIVIDUALS',
                               'ENTITIES'], f'Element parameter tag must be either "INDIVIDUALS" or "ENTITIES". Provided was {element.tag}'
        element_columns = []
        first_child = list(list(element)[0])
        for column in first_child:
            element_columns.append(column.tag)
        return element_columns

    def __init__(self):
        self.list = None
        self.elements_list = []
        self.individuals_df = None
        self.entities_df = None
        self.list_path = 'consolidated.xml'
        self.list_downloaded = False
        self.list_loaded = False

    def create_main_frame(self):
        # Creates the root and main Frame widget, referenced by all other
        # widgets. Not decorated with @interface_method and called separately
        # on main() due to needing to be run first.
        self.root = Tk()
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.title('UNSC Sanctions Checker')
        self.mainframe = ttk.Frame(self.root, padding='4 4 20 20')
        self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

    @interface_method
    def create_load_button(self):
        ttk.Button(self.mainframe, text='Load list',
                   command=self.load_button_func).grid(
            column=0, row=0, sticky=W)

    @interface_method
    def create_list_info(self):
        self.list_info = StringVar(value='List not loaded.')
        ttk.Label(self.mainframe, textvariable=self.list_info).grid(column=0,
                                                                    row=3,
                                                                    rowspan=3,
                                                                    sticky=(
                                                                        N, W))

    @interface_method
    def create_download_list_button(self):
        ttk.Button(self.mainframe, text="Download list",
                   command=self.download_list_button_func).grid(column=0,
                                                                row=1,
                                                                sticky=W)

    @interface_method
    def create_check_update_button(self):
        ttk.Button(self.mainframe, text="Check for update",
                   command=self.check_update_button_func).grid(column=0, row=2,
                                                               sticky=W)

    @interface_method
    def create_name_entry(self):
        self.name = StringVar()
        self.name_entry = ttk.Entry(self.mainframe, width=24,
                                    textvariable=self.name)
        self.name_entry.grid(column=2, row=0, sticky=(W, E))
        ttk.Label(self.mainframe, text='Name:').grid(column=1, row=0, sticky=E)

    @interface_method
    def create_score_entry(self):
        self.score = IntVar(value=90)
        self.score_entry = ttk.LabeledScale(self.mainframe,
                                            variable=self.score, from_=100,
                                            to=0)
        self.score_entry.scale.set(90)
        self.score_entry.grid(column=2, row=1, sticky=(W, E))
        self.score_entry.label.update()
        ttk.Label(self.mainframe, text='Minimum Score Match:').grid(column=1,
                                                                    row=1,
                                                                    sticky=E)

    @interface_method
    def create_search_button(self):
        ttk.Button(self.mainframe, text='Search name',
                   command=self.search_button_func).grid(column=3, row=0,
                                                         sticky=W)

    @interface_method
    def create_matches_treeview(self):
        self.matches_treeview = ttk.Treeview(self.mainframe)
        self.matches_treeview.grid(column=2, row=4, sticky=(N, W, S))
        self.matches_label_var = StringVar(value='No Matches:')
        ttk.Label(self.mainframe, textvariable=self.matches_label_var).grid(
            column=2, row=3, sticky=W)
        self.matches_scrollbar = ttk.Scrollbar(self.mainframe,
                                               orient='vertical',
                                               command=self.matches_treeview.yview)
        self.matches_scrollbar.grid(row=4, column=3, rowspan=10,
                                    sticky=(N, W, S))
        self.matches_treeview.configure(
            yscrollcommand=self.matches_scrollbar.set)

    @interface_method
    def create_generate_report_button(self):
        ttk.Button(self.mainframe, text='Generate report',
                   command=self.generate_report_button_func).grid(row=14,
                                                                  column=2,
                                                                  sticky=NW)

    def call_all_interface_methods(self):
        # Calls all methods decorated with @interface_method
        for name in dir(self):
            attr = getattr(self, name)
            if getattr(attr, '_is_interface_method', False):
                attr()

    def generate_report_button_func(self):
        env = Environment(loader=FileSystemLoader('template'))
        template = env.get_template('report.html')
        template_vars = {
            'name_searched': f'"{self.last_name_searched}"',
            'title': 'UNSC Sanctions list check',
            'score_used': self.last_score_used,
            'matches_info': self.matches_label_var.get(),
            'matches_table': self.df_matches.to_html(),
            'date_of_search': str(date.today())
        }
        report_html = template.render(template_vars)
        pdfkit.from_string(report_html,
                           output_path=filedialog.asksaveasfilename(
                               initialdir=getcwd(),
                               initialfile=f'{self.last_name_searched} UNSC report.pdf',
                               filetypes=[('Pdf files', '*.pdf')]),
                           options={'quiet':''}
                           )

    def download_list_button_func(self):
        if self.list_loaded:
            if messagebox.askyesno(
                    message='A list is already loaded. Would you like to download it again?'):
                self.list_info.set(value='Downloading list, please wait.')
                r = self.connect_to_url()
                self.save_downloaded_list(r)
                if messagebox.askyesno(
                        message='Would you like to load the downloaded list now?\nYou have the option to manually load it later.'):
                    self.autoload_list()
        else:
            self.list_info.set(value='Downloading list, please wait.')
            r = self.connect_to_url()
            self.save_downloaded_list(r)
            if messagebox.askyesno(
                    message='Would you like to load the downloaded list now?\nYou have the option to manually load it later.'):
                self.autoload_list()

    def load_button_func(self):
        self.list_info.set(Application.loading_warning)
        self.load_list()
        self.make_element_dfs()
        self.clean_individuals_df()
        self.append_individuals_full_name()
        self.update_list_info()

    def check_update_button_func(self):
        try:
            r = self.connect_to_url()
            if self.check_list_is_outdated(r):
                if messagebox.askyesno(
                        message='Current list is outdated, download new one?'):
                    self.download_list_button_func()
            else:
                messagebox.showinfo(
                    message=f"List is up-to-date.\nList on UNSC site has {r.headers['Content-Length']} bytes.\nLoaded list has {stat(path=self.list_path)[-4]} bytes.")
        except AttributeError:
            messagebox.showerror(
                message='Could not download list. Try again with a different link or choose it manually')

    def search_button_func(self):
        if self.list_loaded:
            # get fuzzy match results
            self.last_name_searched = str(self.name_entry.get())
            self.last_score_used = self.score.get()
            match_results = process.extractBests(
                query=self.last_name_searched,
                choices=self.individuals_df['FULL_NAME'],
                score_cutoff=self.last_score_used,
                limit=None
            )
            # get lines in df with the matches
            match_lines = [x[-1] for x in match_results]
            self.df_matches = self.individuals_df.iloc[match_lines].copy()
            # add score values column for matches
            self.df_matches.insert(loc=1, column='Score',
                                   value=[x[-2] for x in match_results])
            # create treeview columns and set headings
            columns = self.df_matches.columns.tolist()
            self.matches_treeview['columns'] = columns
            self.matches_treeview['show'] = 'headings'
            for col in columns:
                self.matches_treeview.column(col, width=50)
                self.matches_treeview.heading(col, text=str(col))
            # clear treeview results before adding new ones
            self.matches_treeview.delete(*self.matches_treeview.get_children())
            # Change treeview label to number of matches
            self.matches_label_var.set(
                value=f'{len(self.df_matches)} matches for "{self.last_name_searched}" using score {self.last_score_used}.')
            # add match results to treeview
            for row in self.df_matches.values.tolist():
                self.matches_treeview.insert('', 'end', values=row)
        else:
            messagebox.showerror(message='Sanctions list not loaded.')

    def connect_to_url(self, url=UNSC_sanctions_list_url):
        # Attempts to connect to default url for sanctions list. If url is not
        # valid, calls method again while asking for user input on new url.
        r = requests.get(url)
        if r.status_code == 200 and r.headers['Content-Type'].__contains__(
                'xml') and r.text.__contains__('CONSOLIDATED_LIST'):
            return r
        else:
            if messagebox.askyesno(message=(
                    f'Could not find the list at {url}\nWould you like to try with a different link?')):
                return self.connect_to_url(
                    url=simpledialog.askstring(title='Insert new link',
                                               prompt=f'Please enter new address for UNSC Sanctions list in xml format\nLast address used:{url}'))

    def check_list_is_outdated(self, requests_object):
        # Currently just checking if list on memory is exact same size as list on url.
        # Not to be called by itself, used by check_update_button_func.
        if int(requests_object.headers['Content-Length']) == \
                stat(path=self.list_path)[-4]:
            return False
        else:
            return True

    def save_downloaded_list(self, requests_object):
        try:
            savepath = filedialog.asksaveasfilename(initialdir=getcwd(),
                                                    initialfile='consolidated.xml',
                                                    filetypes=[('Xml files',
                                                                '*.xml')])
            with open(savepath, 'wb') as fd:
                for chunk in requests_object.iter_content(chunk_size=128):
                    fd.write(chunk)
                messagebox.showinfo(
                    message=f'List downloaded from {requests_object.url} and saved at {savepath}')
            self.list_path = savepath
            self.list_downloaded = True
        except AttributeError:
            messagebox.showerror(
                message='Could not download list. Try again with a different link or load the list manually')

    def check_for_list(self):
        if "consolidated.xml" in listdir(getcwd()) or self.list_downloaded:
            return True
        else:
            return False

    def autoload_list(self):
        try:
            if self.check_for_list():
                self.list_info.set(value=Application.loading_warning)
                self.list = et.parse(self.list_path)
                root = self.list.getroot()
                self.elements_list.extend(list(root)[0:2])
                self.make_element_dfs()
                self.clean_individuals_df()
                self.append_individuals_full_name()
                messagebox.showinfo(
                    message=f"Loaded list from file 'consolidated.xml' in dir {getcwd()}")
                self.update_list_info()
            else:
                messagebox.showinfo(
                    message="Could not find list file ('consolidated.xml') in current dir\nPlease load the list manually or get it from the UNSC website")
        except:
            messagebox.showinfo(
                message=f"Could not load file {self.list_path} in current dir\nPlease load the list manually or get it from the UNSC website")
            self.list_info.set(value='List not loaded.')

    def update_list_info(self):
        self.list_loaded = True
        self.list_info.set(
            value=f'List loaded.\nNumber of Individuals: {self.individuals_df.__len__()}\nNumber of Entities: {self.entities_df.__len__()}')

    def load_list(self):
        # Loads a xml file and turns it into a list
        path_window = Tk()
        self.list_path = filedialog.askopenfilename(initialdir=getcwd(),
                                                    filetypes=[('Xml files',
                                                                '*.xml')],
                                                    title='Choose xml list')
        path_window.withdraw()
        path_window.destroy()
        self.list = et.parse(self.list_path)
        etree_root = self.list.getroot()
        self.elements_list.extend(list(etree_root)[0:2])

    def make_element_dfs(self):
        # Takes xml element tree in list form and makes pandas dataframes
        for element in self.elements_list:
            assert element.tag in ['INDIVIDUALS',
                                   'ENTITIES'], f'Element parameter tag must be either "INDIVIDUALS" or "ENTITIES". Provided was {element.tag}'
            df = pd.DataFrame(columns=Application.get_column_list(element))
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
        # Fills name columns NAs with empty strings, turns name columns dtype
        # to str, drops columns with all NAs.
        self.individuals_df.fillna(
            value={'FIRST_NAME': '', 'SECOND_NAME': '', 'THIRD_NAME': '',
                   'FOURTH_NAME': ''}, inplace=True)
        self.individuals_df[
            ['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME', 'FOURTH_NAME']] = \
            self.individuals_df[
                ['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME',
                 'FOURTH_NAME']].astype(
                str)
        self.individuals_df = self.individuals_df.dropna(axis=1, how='all')

    def append_individuals_full_name(self):
        # Creates a full name column for every individual on list, drops used
        # name columns. Full name column is the one used for matching.
        self.individuals_df['FULL_NAME'] = self.individuals_df[
            ['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME', 'FOURTH_NAME']].apply(
            lambda x: ' '.join(x), axis=1)
        self.individuals_df['FULL_NAME'] = self.individuals_df[
            'FULL_NAME'].str.strip()
        while self.individuals_df['FULL_NAME'].str.contains('  ').any():
            self.individuals_df['FULL_NAME'] = self.individuals_df[
                'FULL_NAME'].str.replace('  ', ' ')
        self.individuals_df = self.individuals_df.drop(
            labels=['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME', 'FOURTH_NAME'],
            axis=1)
        self.individuals_df = self.individuals_df[
            ['FULL_NAME'] + [col for col in self.individuals_df.columns if
                             col != 'FULL_NAME']]

    def main(self):
        # Runs all methods to start the program
        self.create_main_frame()
        self.call_all_interface_methods()
        self.autoload_list()
        self.name_entry.focus_force()
        self.root.mainloop()


if __name__ == '__main__':
    app = Application()
    app.main()
