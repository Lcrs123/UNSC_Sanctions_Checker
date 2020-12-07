import xml.etree.ElementTree as et
from datetime import date
from os import getcwd, stat, startfile, path
from tkinter import Tk, filedialog, ttk, messagebox, simpledialog, StringVar, IntVar, Toplevel, Radiobutton, Menu
from tkinter.constants import *
from _imp import is_frozen
import sys

import pandas as pd
import pdfkit
import requests
from fuzzywuzzy import process
from jinja2 import Environment, FileSystemLoader

# importing directories as packages using empty __init__.py files for easier
# pathing.
from unsc_sanctions_checker import data, template
from unsc_sanctions_checker import wkhtmltopdf as _wkhtmltopdf

def main_is_frozen():
    # Used for determining if file is running as script or exe. Returns true if
    # exe. More info: https://pyinstaller.readthedocs.io/en/v3.3.1/runtime-information.html#
    return (hasattr(sys, "frozen") or hasattr(sys, "importers") or is_frozen("__main__"))

def get_main_dir():
    # Get directory if running as exe
    if main_is_frozen():
        return path.dirname(sys.executable)

def interface_method(f):
    # Decorator for identifying interface methods for easier calling
    f._is_interface_method = True
    return f


class Application(object):
    UNSC_sanctions_list_url = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
    if main_is_frozen():
        default_list_path = path.join(get_main_dir(),'data','consolidated.xml')
        default_template_path = path.join(get_main_dir(),'template')
        default_wkhtmltopdf_path = path.join(get_main_dir(),'wkhtmltopdf','wkhtmltopdf.exe')
    else:
        default_list_path = path.join(path.dirname(data.__file__),
                                      'consolidated.xml')
        default_template_path = path.dirname(template.__file__)
        default_wkhtmltopdf_path = path.join(path.dirname(_wkhtmltopdf.__file__),
                                             'wkhtmltopdf.exe')

    @staticmethod
    def get_column_list(element) -> list:
        # takes a xml element tree and returns the childrens names as a column list
        # used on the INDIVIDUALS or ENTITIES element tree branches
        assert element.tag in ['INDIVIDUALS',
                               'ENTITIES'], f'Element parameter tag must be either "INDIVIDUALS" or "ENTITIES". Provided was {element.tag}'
        element_columns = []
        first_child = list(list(element)[0])
        for column in first_child:
            element_columns.append(column.tag)
        return element_columns

    def __init__(self):
        self.elements_list = []
        self.list_path = Application.default_list_path
        self.list_loaded = False
        self.full_list_window_rb_var = None
        self.pdfkit_config = None

    def create_main_frame(self):
        # Creates the root and main Frame widget, referenced by the other subframe
        # widgets. Not decorated with @interface_method and called separately
        # on main() due to needing to be run first. Same reason for subframes.

        self.root = Tk()
        self.root.title('UNSC Sanctions Checker')
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid()

    def create_list_info_frame(self):
        self.list_info_frame = ttk.Frame(self.main_frame, relief=GROOVE,
                                         padding='5 5 5 5')
        self.list_info_frame.grid(row=0, column=0, sticky=NW, rowspan=2)

    def create_search_options_frame(self):
        self.search_options_frame = ttk.Frame(self.main_frame, relief=GROOVE,
                                              padding='5 5 5 5')
        self.search_options_frame.grid(row=0, column=1, sticky=NW)

    def create_search_results_frame(self):
        self.search_results_frame = ttk.Frame(self.main_frame, relief=GROOVE,
                                              padding='5 5 5 5')
        self.search_results_frame.grid(row=1, column=1, sticky=NW)

    def create_all_sub_frames(self):
        # Splitted the interface in three main subframes for easier management
        # of geometry and children. Must be called before the rest of interface
        # methods
        self.create_list_info_frame()
        self.create_search_options_frame()
        self.create_search_results_frame()

    @interface_method
    def create_load_button(self):
        ttk.Button(self.list_info_frame, text='Load list',
                   command=self.load_button_func).grid(
            column=0, row=0, sticky=W)

    @interface_method
    def create_download_list_button(self):
        ttk.Button(self.list_info_frame, text="Download list",
                   command=self.download_list_button_func).grid(column=0,
                                                                row=1,
                                                                sticky=W)

    @interface_method
    def create_check_update_button(self):
        ttk.Button(self.list_info_frame, text="Check for update",
                   command=self.check_update_button_func).grid(column=0, row=2,
                                                               sticky=W)

    @interface_method
    def create_list_info(self):
        self.list_info = StringVar(value='List not loaded.')
        ttk.Label(self.list_info_frame, textvariable=self.list_info).grid(
            column=0, row=3, sticky=W)

    @interface_method
    def create_show_list_button(self):
        self.show_list_button = ttk.Button(master=self.list_info_frame,
                                           text='Show list',
                                           command=self.show_list_button_func).grid(
            column=0, row=4, sticky=W)

    @interface_method
    def create_name_entry(self):
        self.name_to_search = StringVar()
        self.name_entry = ttk.Entry(self.search_options_frame,
                                    textvariable=self.name_to_search)
        self.name_entry.grid(column=1, row=1, sticky=(W, E), columnspan=2)
        ttk.Label(self.search_options_frame, text='Name:').grid(column=0,
                                                                row=1,
                                                                sticky=E)
        self.name_entry.bind(sequence='<Return>',func=self.search_button_func)

    @interface_method
    def create_search_button(self):
        self.search_button = ttk.Button(self.search_options_frame, text='Search',
                   command=self.search_button_func).grid(column=3, row=1,
                                                         sticky=W)

    @interface_method
    def create_score_entry(self):
        ttk.Label(self.search_options_frame, text='Minimum Score Match:').grid(
            column=0,
            row=2,
            sticky=E)
        self.score = IntVar(value=90)
        self.score_entry = ttk.LabeledScale(self.search_options_frame,
                                            variable=self.score, from_=100,
                                            to=0)
        self.score_entry.scale.set(90)
        self.score_entry.grid(column=1, row=2, sticky=(W, E), columnspan=2)
        self.score_entry.label.update()

    @interface_method
    def create_choose_list_buttons(self):
        ttk.Label(master=self.search_options_frame,
                  text='List to search:').grid(row=0, column=0, sticky=E)
        self.list_chosen = StringVar(value='Individuals')
        self.individuals_list_rb = ttk.Radiobutton(
            master=self.search_options_frame, text='Individuals',
            var=self.list_chosen, value='Individuals')
        self.entities_list_rb = ttk.Radiobutton(
            master=self.search_options_frame, text='Entities',
            var=self.list_chosen, value='Entities')
        self.individuals_list_rb.grid(row=0, column=1, sticky=W)
        self.entities_list_rb.grid(row=0, column=2, sticky=W)

    @interface_method
    def create_matches_treeview(self, full_list=False):
        # creates the treeview for the match results. Use with full_list = True
        # to create the treeview for showing the entire list in a new window
        if full_list == False:
            self.matches_label_var = StringVar(value='No Matches:')
            ttk.Label(self.search_results_frame,
                      textvariable=self.matches_label_var).grid(column=0,
                                                                row=0,
                                                                sticky=W)
            self.matches_treeview = ttk.Treeview(self.search_results_frame)
            self.matches_treeview.grid(column=0, row=1, sticky=(N, W, S))
            self.matches_scrollbar = ttk.Scrollbar(self.search_results_frame,
                                                   orient='vertical',
                                                   command=self.matches_treeview.yview)
            self.matches_scrollbar.grid(column=1, row=1, sticky=(N, W, S))
            self.matches_treeview.configure(
                yscrollcommand=self.matches_scrollbar.set)
        else:
            self.full_list_label_var = StringVar(value='')
            ttk.Label(self.full_list_window,
                      textvariable=self.full_list_label_var).grid(column=1,
                                                                  row=0,
                                                                  sticky=W)
            self.full_list_treeview = ttk.Treeview(self.full_list_window)
            self.full_list_treeview.grid(column=1, row=1, sticky=(N, W, S))
            self.full_list_scrollbar = ttk.Scrollbar(self.full_list_window,
                                                     orient='vertical',
                                                     command=self.full_list_treeview.yview)
            self.full_list_scrollbar.grid(column=2, row=1, sticky=(N, W, S))
            self.full_list_treeview.configure(
                yscrollcommand=self.full_list_scrollbar.set)

    @interface_method
    def create_save_report_button(self):
        ttk.Button(self.search_results_frame, text='Save report',
                   command=self.save_report_button_func).grid(row=2,
                                                              column=0,
                                                              sticky=NW)

    @interface_method
    def create_menus(self):
        self.menu = Menu(master=self.root)
        self.file_menu = Menu(master=self.menu,tearoff=0)
        self.file_menu.add_command(label='Load list',command=self.load_button_func)
        self.file_menu.add_command(label='Download list',command=self.download_list_button_func)
        self.file_menu.add_command(label='Check update',command=self.check_update_button_func)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Save report', command=self.save_report_button_func)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Exit',command=self.root.quit)
        self.menu.add_cascade(label='File',menu=self.file_menu)
        self.root.config(menu=self.menu)

    def call_all_interface_methods(self):
        # Calls all methods decorated with @interface_method
        for name in dir(self):
            attr = getattr(self, name)
            if getattr(attr, '_is_interface_method', False):
                attr()

    def show_list_button_func(self):
        self.full_list_window = Toplevel(master=self.main_frame,
                                         name='full_list_window')
        if self.full_list_window_rb_var == None:
            self.full_list_window_rb_var = StringVar(value='Individuals')
        self.create_matches_treeview(full_list=True)
        Radiobutton(master=self.full_list_window, text='Individuals',
                    var=self.full_list_window_rb_var, value='Individuals',
                    indicatoron=False, command=self.display_full_list).grid(
            row=0, column=0, sticky=NW)
        Radiobutton(master=self.full_list_window, text='Entities',
                    var=self.full_list_window_rb_var, value='Entities',
                    indicatoron=False, command=self.display_full_list).grid(
            row=1, column=0, sticky=NW)
        self.display_full_list()

    def display_full_list(self):
        # TODO split into smaller functions
        self.full_list_treeview.delete(*self.full_list_treeview.get_children())
        chosen_list_df = self.list_choice_to_dataframe(
            self.full_list_window_rb_var.get())
        # create treeview columns and set headings
        columns = chosen_list_df.columns.tolist()
        self.full_list_treeview['columns'] = columns
        for col in columns:
            self.full_list_treeview.heading(col, text=str(col))
            self.full_list_treeview.column(col, width=len(col) * 10)
        self.full_list_treeview['show'] = 'headings'
        # Change treeview label to number of matches
        self.full_list_label_var.set(
            value=f'Showing all {len(chosen_list_df)} entries in {self.full_list_window_rb_var.get()} list.')
        # add match results to treeview
        for row in chosen_list_df.values.tolist():
            self.full_list_treeview.insert('', 'end', values=row)

    def save_report_button_func(self):
        if self.list_loaded and hasattr(self, 'last_name_searched'):
            html_report = self.make_html_report()
            self.output_report(html_report)
        else:
            messagebox.showerror(
                message='List not loaded or no name searched yet')

    def download_list_button_func(self):
        if self.list_loaded:
            if messagebox.askyesno(
                    message='A list is already loaded. Would you like to download it again?'):
                self.connect_save_load()
        else:
            self.connect_save_load()

    def load_button_func(self):
        self.load_list()

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

    def search_button_func(self,event):
        # TODO split method into smaller functions
        if self.list_loaded:
            # save search info
            self.last_name_searched = str(self.name_entry.get())
            self.last_score_used = self.score.get()
            self.last_list_chosen = self.list_chosen.get()
            self.df_matches = self.get_match_results(
                chosen_list=self.last_list_chosen)
            # clear treeview results before adding new ones
            self.matches_treeview.delete(*self.matches_treeview.get_children())
            # create treeview columns and set headings
            columns = self.df_matches.columns.tolist()
            self.matches_treeview['columns'] = columns
            for col in columns:
                self.matches_treeview.heading(col, text=str(col))
                self.matches_treeview.column(col, width=len(col) * 10)
            self.matches_treeview['show'] = 'headings'
            # Change treeview label to number of matches
            self.matches_label_var.set(
                value=f'{len(self.df_matches)} match(es) for "{self.last_name_searched}" on {self.last_list_chosen} list using score {self.last_score_used}.')
            # add match results to treeview
            for row in self.df_matches.values.tolist():
                self.matches_treeview.insert('', 'end', values=row)
        else:
            messagebox.showerror(
                message='Sanctions list not loaded. Please load a list before trying to search')

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

    def list_choice_to_dataframe(self, chosen_list):
        lists_dataframe_dict = {'Individuals': self.individuals_df,
                                'Entities': self.entities_df}
        return lists_dataframe_dict[chosen_list]

    def ask_open_report(self, output_path):
        if messagebox.askyesno(
                message=f'Report saved at {output_path}.\nWould you like to open the report?'):
            startfile(filepath=output_path)

    def make_html_report(self):
        env = Environment(
            loader=FileSystemLoader(Application.default_template_path))
        template = env.get_template('report.html')
        template_vars = {
            'name_searched': f'"{self.last_name_searched}"',
            'title': 'UNSC Sanctions list check',
            'score_used': self.last_score_used,
            'matches_info': self.matches_label_var.get(),
            'matches_table': self.df_matches.to_html(),
            'date_of_search': str(date.today()),
            'list_searched': self.last_list_chosen,
            'list_date': self.list_date
        }
        html_report = template.render(template_vars)
        return html_report

    def output_report(self, html_report):
        try:
            output_path = self.output_report_path('pdf')
            if self.pdfkit_config == None:
                self.pdfkit_config = pdfkit.configuration(
                    wkhtmltopdf=Application.default_wkhtmltopdf_path)
            pdfkit.from_string(html_report,
                               output_path=output_path,
                               options={'quiet': ''},
                               configuration=self.pdfkit_config
                               )
            self.ask_open_report(output_path)
        except OSError:
            if messagebox.askyesno(
                    message="Could not save report as pdf.\n\n Package wkhtmltopdf appears to not be installed correctly. Package file wkhtmltopdf.exe should be in working directory.\n\nSave report in html format?"):
                output_path = self.output_report_path('html')
                with open(output_path, 'w', encoding='UTF-8') as f:
                    f.write(html_report)
                self.ask_open_report(output_path)

    def output_report_path(self, filetype: str):
        assert filetype in ['pdf', 'html']
        output_path = filedialog.asksaveasfilename(
            initialdir=getcwd(),
            initialfile=f'{self.last_score_used}-{self.last_name_searched}-report.{filetype}',
            filetypes=[(f'{filetype.capitalize()} files', f'*.{filetype}')]
        )
        return output_path

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

    def connect_save_load(self):
        self.list_info.set(value='Downloading list, please wait.')
        r = self.connect_to_url()
        self.save_downloaded_list(r)
        if messagebox.askyesno(
                message='Would you like to load the downloaded list now?\nYou have the option to manually load it later.'):
            self.load_list(auto=True)

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
            savepath = filedialog.asksaveasfilename(
                initialdir=path.abspath(path.dirname(self.list_path)),
                initialfile='consolidated.xml',
                filetypes=[('Xml files',
                            '*.xml')]
            )
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
        if path.exists(self.list_path):
            return True
        else:
            return False

    def load_list(self, auto=False, no_interface=False):
        # auto is used on main() for trying to load the list automatically from
        # default path. no_interface is used for debugging and development
        if auto == False:
            path_window = Tk()
            self.list_path = filedialog.askopenfilename(initialdir=getcwd(),
                                                        filetypes=[
                                                            ('Xml files',
                                                             '*.xml')],
                                                        title='Choose list in xml format'
                                                        )
            path_window.withdraw()
            path_window.destroy()
        try:
            if self.check_for_list():
                if no_interface == False:
                    self.list_info.set(value='Loading list, please wait')
                self.etree_to_list()
                self.make_element_dfs()
                self.clean_individuals_df()
                self.clean_entities_df()
                self.append_individuals_full_name()
                messagebox.showinfo(
                    message=f"Loaded list from file {self.list_path}")
                if no_interface == False:
                    self.update_list_info()
                else:
                    self.update_list_info(no_interface=no_interface)
            else:
                messagebox.showinfo(
                    message=f"Could not find list file ('consolidated.xml') in directory {path.abspath(path.dirname(self.list_path))}\nPlease load the list manually or get it from the UNSC website")
        except:
            messagebox.showinfo(
                message=f"Could not load file {self.list_path}.\nPlease load the list manually or get it from the UNSC website")
            if no_interface == False:
                self.list_info.set(value='List not loaded.')

    def etree_to_list(self):
        self.etree = et.parse(self.list_path)
        root = self.etree.getroot()
        self.elements_list.extend(list(root)[0:2])

    def update_list_info(self, no_interface=False):
        self.list_loaded = True
        self.list_date = self.get_list_date()
        if no_interface == False:
            self.list_info.set(
                value=f'List loaded.\n\nNumber of Individuals: {self.individuals_df.__len__()}\nNumber of Entities: {self.entities_df.__len__()}\n\nList date: {self.list_date.isoformat()}')

    def get_list_date(self):
        root = self.etree.getroot()
        date_str = root.items()[1][1]
        iso_date = date.fromisoformat(date_str[:10])
        return iso_date

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
        self.individuals_df[:,'LISTED_ON'] = self.individuals_df['LISTED_ON'].astype(
            dtype='datetime64').dt.date
        self.individuals_df = self.individuals_df.dropna(axis=1, how='all')

    def clean_entities_df(self):
        # drop columns with all NAs, put FIRST_NAME column first, change listed
        # on dtype
        self.entities_df = self.entities_df.dropna(axis=1, how='all')
        self.entities_df[:,'LISTED_ON'] = self.entities_df['LISTED_ON'].astype(
            dtype='datetime64').dt.date
        self.entities_df = self.entities_df[
            ['FIRST_NAME'] + [col for col in self.entities_df.columns if
                              col != 'FIRST_NAME']]



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
        self.create_all_sub_frames()
        self.call_all_interface_methods()
        self.load_list(auto=True)
        self.name_entry.focus_force()
        self.root.mainloop()


def run():
    app = Application()
    app.main()


if __name__ == '__main__':
    run()
