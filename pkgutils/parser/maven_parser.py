import logging
import xml.etree.ElementTree as xml
from .parser import Parser
from ..globals import MAJOR_VERSION_REGEX

class MavenParser(Parser):

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def dependencies_to_purls(self, dependencies_object, major_version_only=False):
        """
        Convert Java dependencies names to the universal Package URL (PURL) format

        arguments:
            :dependencies: Entire pom.xml text file

        returns:
            list of dependencies in P-URL format
        """

        namespaces = {'xmlns': 'http://maven.apache.org/POM/4.0.0'}

        try:
            root = xml.fromstring(dependencies_object, parser=xml.XMLParser(encoding='utf-8'))
            dependencies = root.findall(".//xmlns:dependency", namespaces=namespaces)

            if dependencies:
                purl_dependencies = []

                for dependency in dependencies:
                    groupId = dependency.find("xmlns:groupId", namespaces=namespaces)
                    artifactId = dependency.find("xmlns:artifactId", namespaces=namespaces)
                    version = dependency.find("xmlns:version", namespaces=namespaces)

                    # WARNING: this is needed to treat '' as not None
                    # TODO: verify this claim
                    if groupId is None or artifactId is None:
                        continue

                    # WARNING: this is needed to treat '' as not None
                    # TODO: verify this claim
                    if version is not None:
                        value = version.text

                        if value.find('$') >= 0:
                            value = ''

                        if major_version_only and value:
                            # Extract the major version number from the version string
                            result = MAJOR_VERSION_REGEX.search(value)
                            if not result:
                                continue
                            value = result.group()

                        purl_dependencies.append(f'pkg:maven/{groupId.text}/{artifactId.text}@{value}')
                    else:
                        purl_dependencies.append(f'pkg:maven/{groupId.text}/{artifactId.text}')

                return purl_dependencies

        except xml.ParseError as e:
            self.logger.error(e)
            return []



        