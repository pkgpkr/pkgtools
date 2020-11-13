from ..globals import MAJOR_VERSION_REGEX, JAVASCRIPT, PYTHON, JAVA

class Parser(object):
    def __init__(self):
        pass

    def dependencies_to_purls(self, dependencies_object, major_version_only=False):
        pass

    def decompose_purl_string(self, purl):
        package_info = {}

        if purl:
            name_and_version = str(purl).split('@')
            if len(name_and_version) >= 1:
                package_info["name"] = name_and_version[0]

            if len(name_and_version) >= 2:
                package_info["full_version"] = name_and_version[1]

                result = MAJOR_VERSION_REGEX.search(package_info["full_version"])
                if result:
                    package_info["major_version"] = result.group()

        return package_info