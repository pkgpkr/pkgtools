from .npm_parser import NpmParser
from .maven_parser import MavenParser
from .pypi_parser import PyPiParser
from ..globals import JAVASCRIPT, PYTHON, JAVA

class ParserFactory(object):
    def __init__(self):
        pass

    @staticmethod
    def get_parser(language):
        if language == JAVASCRIPT:
            return NpmParser()
        elif language == PYTHON:
            return PyPiParser()
        elif language == JAVA:
            return MavenParser()