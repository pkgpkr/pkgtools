import json
import logging
from .parser import Parser
from ..globals import MAJOR_VERSION_REGEX

class NpmParser(Parser):

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def dependencies_to_purls(self, dependencies, major_version_only=False):
        """
        Convert Javascript dependency names to the universal Package URL (PURL) format

        arguments:
            :dependencies: Array of name@version like names

        returns:
            list of dependencies in P-URL format
        """

        try:
            dependencies = json.loads(dependencies)
        except json.decoder.JSONDecodeError:
            raise ValueError()

        purl_dependencies = []

        if dependencies.get('dependencies'):
            for name, version in dependencies.get('dependencies').items():
                # Remove ~ and ^ from versions
                clean_version = str(version).strip('~').strip('^')

                if major_version_only and clean_version:
                    # Extract the major version number from the version string
                    result = MAJOR_VERSION_REGEX.search(clean_version)
                    if not result:
                        continue
                    clean_version = result.group()

                purl_dependencies.append(f'pkg:npm/{name}@{clean_version}')

        return purl_dependencies
