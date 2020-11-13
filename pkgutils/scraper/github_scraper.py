import json
import logging
import requests
from datetime import datetime

from ..globals import SUPPORTED_LANGUAGES, GITHUB_GRAPHQL_URL, GITHUB_USER_INFO_URL


class GithubScraper(object):

    def __init__(self, token):

        self.request_headers = {"Authorization": "Bearer " + token}

        GithubScraper._MAX_NODES_PER_LOOP = 100
        GithubScraper._GITHUB_V4_URL = 'https://api.github.com/graphql'

        self.logger = logging.getLogger(__name__)

    def get_user_info(self):
        """
        Get the user info associated with the given GitHub token

        arguments:
            :token: GitHub API token

        returns:
            JSON object with user info
        """

        url = GITHUB_USER_INFO_URL
        res = requests.get(url, headers=self.request_headers)
        return res.json()

    def get_content_of_object(self, owner: str, repo: str, branch: str, file_path: str) -> str:
        """ Fetch the content of the file specified.
        Args:
            owner: owner of the repo (must match the one in repo uri)
            repo: name of the repository  
            branch: name of specific branch 
            file_path: relative path to file that follows branch name in uri

        Return:
            str: content of the file
        """

        # Query to get package info
        query = """
                    query GetDependencies($userString: String!, $repositoryString: String!, $expression: String!) {
                        repository(name:$repositoryString, owner:$userString){
                            name
                            refs(first: 100, refPrefix: "refs/heads/") {
                                nodes {
                                    name
                                }
                            }
                            object(expression:$expression){
                            ... on Blob {
                                text
                            }
                            }
                        }
                    }
                """

        # Vars for the query
        variables = f"""{{"userString": "{owner}",
                        "repositoryString": "{repo}",
                        "expression": "{branch}:{file_path}"}}
                    """

        # Construct payload for graphql
        payload = {'query': query,
                   'variables': variables}

        # Call v4 API
        res = requests.post(
            GITHUB_GRAPHQL_URL, headers=self.request_headers, data=json.dumps(payload))

        # Fetch the text that contains the package.json inner text
        return res.json()['data']['repository']['object']['text']

    def get_dependency_file_paths(self, name_with_owner: str, branch: str) -> list:
        """ Fetch the all depende of the file specified.
        Args:
            name_with_owner (str): name with owner of the repo to fetch paths from

            branch(str): name of the branch

        Return:
            list: list of dicts {"path": string, "language": string} to all dependencies files
        """

        # Split qualified repo name into user nae and repo name
        user_name, repo_name = name_with_owner.split('/')

        # Call API to get the structure of the repo (specific branch) i.e. tree # TODO default branch
        find_manifest_url = f"https://api.github.com/repos/{user_name}/{repo_name}/git/trees/{branch}?recursive=1"
        repo_path_obj = requests.get(
            find_manifest_url, headers=self.request_headers)
        repo_path_json = repo_path_obj.json()
        # Fetch the attribute needed that has tree info
        tree = repo_path_json['tree']

        # Placeholders objects
        paths_list = []

        # For each language
        for lang in SUPPORTED_LANGUAGES.keys():
            # Create expression with branch name in it
            file_name_to_find = SUPPORTED_LANGUAGES[lang]['dependencies_file']

            # Loop thru leafs looking for the dependencies file name match
            for leaf in tree:
                path_to_manifest = leaf['path']
                if file_name_to_find in path_to_manifest:
                    paths_list.append({"path": path_to_manifest,
                                       "language": lang})  # Append if found

        return paths_list

    def get_repo_info(self, repo_owner, repo_name):
        """
        Get details for one repo

        name_with_owner (str): Repository name

        Return:
            {
                "nameWithOwner": string,
                "url": "string",
                "watchers": {"totalCount": int},
                "updatedAt": "string",
                "primaryLanguage": {
                    "name": "string"
                },
                "languages": {
                    "nodes": [
                        {
                            "name": "string"
                        }
                    ]
                },
                "defaultBranchRef': {
                    "name": "string"
                },
                "refs": {
                    "nodes": [
                        {
                            "name": "string"
                        }
                    ]
                }
            }
        """

        try:

            query = """
                query RepositoryDetails($repo_owner:String!, $repo_name:String!) {
                    repository(owner: $repo_owner, name: $repo_name) {
                        nameWithOwner
                        url
                        defaultBranchRef{
                            name
                        }
                        watchers {
                            totalCount
                        }
                        updatedAt
                        primaryLanguage {
                            name
                        }
                        languages(first: 100, orderBy: {direction: DESC, field: SIZE}) {
                            nodes {
                                name
                            }
                        }
                        refs(first: 100, refPrefix: "refs/heads/") {
                            nodes {
                                name
                            }
                        }
                    }
                }
                """

            variables = {
                "repo_owner": repo_owner,
                "repo_name": repo_name
            }

            request = requests.post(GithubScraper._GITHUB_V4_URL,
                                    json={'query': query,
                                          'variables': variables},
                                    headers=self.request_headers)

            result = request.json()

            repo = {}
            if result['data']['repository']:

                repo = result['data']['repository']

                # Filtering language to ones we support
                if repo['primaryLanguage'] and repo['primaryLanguage']['name'].lower() in SUPPORTED_LANGUAGES.keys():
                    repo['language'] = repo['primaryLanguage']['name'].lower()
                else:
                    repo['language'] = 'unsupported'

            return repo

        except (ValueError, TypeError, KeyError) as exc:
            # pylint: disable=line-too-long
            self.logger.warning(
                f"Could not fetch repository details: {exc}: {result}")

    def get_repos(self, start_date: datetime.date = None, end_date: datetime.date = None, **kwargs):
        """
        Gets repos. Limit 1000.

        kwargs (languages: list = [], owner: str = None, stars=5)

        If owner argument is passed, all other arguments will be ignored.

        Return:
            nodes (generator) {"nameWithOwner": string,
                               "url": "string",
                               "watchers': {"totalCount": int},
                               "defaultBranchRef': {
                                  "name": "string"
                               }
        """

        languages = kwargs.get('languages')
        if not languages:
            languages = SUPPORTED_LANGUAGES

        owner = kwargs.get('owner')
        stars = kwargs.get('stars')

        # Contruct the date range
        date_range_str = None
        if start_date and end_date:
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            date_range_str = f"{start_date_str}..{end_date_str}"

        # While loop to use cursor to get paginated repos
        cursor = None

        if owner:
            try:
                user_repos_query = """
                    query GetUserRepositories($userString: String!) {
                        user(login: $userString) {
                            repositories(first:100) {
                                nodes {
                                    updatedAt
                                    nameWithOwner
                                    primaryLanguage {
                                        name
                                    }
                                }
                            }
                        }
                    }
                    """

                variables = {
                    "userString": owner
                }

                request = requests.post(GithubScraper._GITHUB_V4_URL,
                                        json={'query': user_repos_query,
                                              'variables': variables},
                                        headers=self.request_headers)

                result = request.json()

                if result['data']['user']['repositories']['nodes']:

                    # Yield nodes for each repo (generator pattern)
                    for node in result['data']['user']['repositories']['nodes']:

                        # Filtering language to ones we support
                        if node['primaryLanguage'] and node['primaryLanguage']['name'].lower() in SUPPORTED_LANGUAGES.keys():
                            node['language'] = node['primaryLanguage']['name'].lower()
                        else:
                            node['language'] = 'unsupported'

                        # Pass control back to the client
                        yield node

            except (ValueError, TypeError, KeyError) as exc:
                # pylint: disable=line-too-long
                self.logger.warning(
                    f"Could not run query starting at {cursor} for {date_range_str}: {exc}: {result}")
        else:
            while True:
                try:
                    search_query = """
                        query SearchMostTop10Star($queryString: String!, $maybeAfter: String, $numberOfNodes: Int) {
                            search(query: $queryString, type: REPOSITORY, first: $numberOfNodes, after: $maybeAfter) {
                                edges {
                                    node {
                                        ... on Repository {
                                            nameWithOwner
                                            url
                                            defaultBranchRef{
                                                name
                                            }
                                            watchers {
                                                totalCount
                                            }
                                            updatedAt
                                            primaryLanguage {
                                                name
                                            }
                                            languages(first: 3, orderBy: {direction: DESC, field: SIZE}) {
                                                nodes {
                                                    name
                                                }
                                            }
                                        }
                                    }
                                    cursor
                                }
                                repositoryCount
                            }
                        }
                        """

                    language_filter = ' '.join(
                        [f"language:{language}" for language in languages])
                    stars_filter = f"stars:>{stars}" if stars else 'stars:>1'
                    owner_filter = f"user:{owner}" if owner else ''
                    date_range_filter = f"pushed:{date_range_str}" if date_range_str else ''

                    variables = {
                        "queryString": ' '.join([language_filter, stars_filter, owner_filter, date_range_filter]),
                        "maybeAfter": cursor,
                        "numberOfNodes": GithubScraper._MAX_NODES_PER_LOOP
                    }

                    request = requests.post(GithubScraper._GITHUB_V4_URL,
                                            json={'query': search_query,
                                                  'variables': variables},
                                            headers=self.request_headers)

                    result = request.json()

                    if result['data']['search']['edges']:
                        # Get the next cursor
                        cursor = result['data']['search']['edges'][-1]['cursor']

                        # Yield nodes for each repo (generator pattern)
                        for edge in result['data']['search']['edges']:

                            # Filtering language to ones we support
                            if edge['node']['primaryLanguage'] and edge['node']['primaryLanguage']['name'].lower() in SUPPORTED_LANGUAGES.keys():
                                edge['node']['language'] = edge['node']['primaryLanguage']['name'].lower(
                                )
                            else:
                                edge['node']['language'] = 'unsupported'

                            # Pass control back to the client
                            yield edge['node']
                    else:
                        # Processed all nodes
                        break

                except (ValueError, TypeError, KeyError) as exc:
                    # pylint: disable=line-too-long
                    self.logger.warning(
                        f"Could not run query starting at {cursor} for {date_range_str}: {exc}: {result}")
                    break
