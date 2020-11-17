import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="UNSC_Sanctions_Checker-Lcrs123", # Replace with your own username
    version="0.0.1",
    author="Lucas Camillo",
    author_email="lucascamillo333@hotmail.com",
    description="UNSC Sanctions checker with a GUI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Lcrs123/UNSC_Sanctions_Checker",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: GNU 3",
        "Operating System :: Windows",
    ],
    python_requires='>=3.7',
)