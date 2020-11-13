from setuptools import setup
import sys


def parse_requirements(filename: str) -> list:
      """ Parse requirements.txt file for values and skip comment lines """
      with open(filename) as req_file:
            return [line.strip() for line in req_file.readlines() if not line.startswith('#')]

def version_check():
      if sys.version_info < (3, 6):
            sys.exit(
                f"Python 3.6 required. Your version: {sys.version_info.major}.{sys.version_info.minor}")


def setup_package():
      setup(name='pkgutils',
            version='0.1.1.dev',
            description='Easy scraping and parsing of package dependencies.',
            packages=['pkgutils', 'pkgutils.scraper', 'pkgutils.parser'],
            install_requires=parse_requirements('requirements.txt'),
            test_suite = 'nose.collector',
            test_require=parse_requirements('requirements.txt')
            )

if  __name__ == "__main__":
      version_check()
      setup_package()
