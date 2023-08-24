from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in diagram_app/__init__.py
from diagram_app import __version__ as version

setup(
	name="diagram_app",
	version=version,
	description="Diagam app for doctype and workflow",
	author="aymen nasser",
	author_email="aymenit2008@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
