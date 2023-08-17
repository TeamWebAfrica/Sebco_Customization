from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in sebco_customization/__init__.py
from sebco_customization import __version__ as version

setup(
	name="sebco_customization",
	version=version,
	description="Customization for Sebco Limited",
	author="Kipngetich Ngeno",
	author_email="khalifngeno@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
