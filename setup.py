from setuptools import setup, find_packages


with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name='PyFIT',
    version='0.0.1',
    url='https://github.com/JoanPuig/PyFIT',
    license='Apache License 2.0',
    author='Joan Puig',
    author_email='joan.puig@gmail.com',
    description='PyFIT is a library that allows reading .FIT files into Python',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(), install_requires=['pytest']
)
