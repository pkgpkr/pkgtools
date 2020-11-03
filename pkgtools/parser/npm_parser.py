import logging


class NpmParser(object):

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def dependencies_to_purls(self, dependencies):
        """
        Convert Javascript dependency names to the universal Package URL (PURL) format

        arguments:
            :dependencies: Array of name@version like names

        returns:
            list of dependencies in P-URL format
        """

        purl_dependencies = []

        for name, version in dependencies.items():
            # Remove ~ and ^ from versions
            clean_version = version.strip('~').strip('^')

            purl_dependencies.append(f'pkg:npm/{name}@{clean_version}')

        return purl_dependencies
