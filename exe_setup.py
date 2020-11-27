from distutils.core import setup
import py2exe

setup(
    windows=[
        {
         'script':'unsc_sanctions_checker/__init__.py',
         'dest_base':'unsc_sanctions_checker'
        }
    ],
    data_files=[('data',['unsc_sanctions_checker/data/consolidated.xml']),
        ('template',['unsc_sanctions_checker/template/report.html']),
        ('wkhtmltopdf',['unsc_sanctions_checker/wkhtmltopdf/wkhtmltopdf.exe'])
    ],
    zipfile=None,
    options={
        'py2exe':{
            'dist_dir':'exe_dist/',
            'optimize':2
        }
    }
)