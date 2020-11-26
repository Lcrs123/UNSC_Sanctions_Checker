import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = []
with open('requirements.txt','r') as fh:
    for line in fh.readlines():
        requirements.append(line.replace('\n',''))

setuptools.setup(
    name="UNSC_Sanctions_Checker",
    version="3.0.0",
    author="Lucas Camillo",
    author_email="lucascamillo333@hotmail.com",
    description="UNSC Sanctions checker with a GUI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Lcrs123/UNSC_Sanctions_Checker",
    py_modules=["UNSC_Sanctions_Checker"],
    license='GNU',
    classifiers=["Programming Language :: Python :: 3",
                 "Development Status :: 4 - Beta",
                 "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
                 "Operating System :: Microsoft :: Windows"],
    python_requires='>=3.7',
    install_requires=requirements,
    data_files=[
        ('data',['data/consolidated.xml']),
        ('template',['template/report.html']),
        ('',['wkhtmltopdf.exe'])
    ]
)