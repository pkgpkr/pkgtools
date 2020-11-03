from setuptools import setup

setup(name='pkgtools',
      version='0.1',
      description='Easy scraping and parsing of package dependencies.',
      packages=['pkgtools', 'pkgtools.scraper'],
      install_requires=['requests']  # TODO this should grab from requirements.txt
      
      )