import requirements
import logging
from .parser import Parser
from ..globals import MAJOR_VERSION_REGEX

class PyPiParser(Parser):

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def dependencies_to_purls(self, dependencies, major_version_only=False):
        """
        Convert Python dependencies names to the universal Package URL (PURL) format

        arguments:
            :dependencies: List of name straight from requirements text file

        returns:
            list of dependencies in P-URL format
        """

        purl_dependencies = []

        for dependency in dependencies.split('\n'):

            # Strip out whitespace
            dep = dependency.strip()

            # Filter out empty lines and comments
            if not dep.strip() or dep.startswith('#') or 'git+'.casefold() in dep.casefold():
                continue

            # Parse using 3rd party function
            try:
                # Get the first element because we're parsing dependencies one at a time
                parsed = list(requirements.parse(dep))[0]
            except Exception as e:
                continue

            name = parsed.name

            clean_version = None
            if parsed.specs:
                for spec in parsed.specs:
                    # TODO: Try to do more intelligent version parsing here
                    # check the specifier (e.g. >=, <) and grabs first one with equal meaning it's legal version allowed
                    if spec and '=' in spec[0]:
                        # this is the version which is idx 1 in the tuple
                        clean_version = spec[1]
                        break

            if major_version_only and clean_version:
                # Extract the major version number from the version string
                result = MAJOR_VERSION_REGEX.search(clean_version)
                if not result:
                    continue
                clean_version = result.group()

            purl_dependencies.append(f'pkg:pypi/{name}')

            if clean_version:
                purl_dependencies[-1] += f'@{clean_version}'

        return purl_dependencies
