import requirements
import logging


class PyPiParser(object):

    def __init__(self):

        self.logger = logging.getLogger(__name__)

    def dependencies_to_purls(self, dependencies):
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
            if not dep.strip() or dep.startswith('#'):
                continue

            # Parse using 3rd party function
            try:
                parsed = list(requirements.parse(dep))[0]
            except Exception as e:
                continue

            name = parsed.name

            clean_version = None
            if parsed.specs:
                for spec in parsed.specs:
                    # check the specifier (e.g. >=, <) and grabs first one with equal meaning it's legal version allowed
                    if '=' in spec[0]:
                        # this is the version which is idx 1 in the tuple
                        clean_version = spec[1]
                        break

            purl_dependencies.append(f'pkg:pypi/{name}')

            if clean_version:
                purl_dependencies[-1] += f'@{clean_version}'

        return purl_dependencies
