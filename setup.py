from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in boya_integration/__init__.py
from boya_integration import __version__ as version

setup(
	name="boya_integration",
	version=version,
	description="Boya Integration",
	author="Kipngetich Ngeno",
	author_email="khalifngeno@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
