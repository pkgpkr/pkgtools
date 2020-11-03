import logging
import requests
from datetime import datetime

class GithubScraper(object):

    def __init__(self, token):
    
        self.request_headers = {"Authorization": "Bearer " + token}

        GithubScraper._MAX_NODES_PER_LOOP = 100
        GithubScraper._GITHUB_V4_URL = 'https://api.github.com/graphql'



        self.logger = logging.getLogger(__name__)


    def get_content_by_uri(self, uri: str) -> str:
        """ Fetch the conten of the file specified. """

        # TODO
        return

    def get_uris_by_repo(self, repo: str) -> list:
        """ Fetch the all depende of the file specified. """

        # TODO
        return

    def get_dependecies_uris_by_repo(self, repo: str, dependencies_file_names: list = None) -> list:
        """ Fetch the all depende of the file specified. """

        uris = self.get_uris_by_repo(repo)

        # TODO filter etc.
        return uris

    def get_repos(self, start_date: datetime.date = None, end_date: datetime.date = None, **kwargs):
        """


        kwargs (language: str = None, owner: str = None, stars=5 ? ) TODO

        Return:
            nodes (generator) {'nameWithOwner': string, 'url': string, 'watchers': {'totalCount': int}}
        """
                        
        language = kwargs.get('language')
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

        while True:

            try:
                """
                Fetch a single page of repositories for the given month

                arguments:
                    :node_per_loop: number of nodes in batch
                    :daily_search_str: GitHub v4 API search string, e.g specify start/end
                    :cursor: DB cursor
                    :language: ecosystem language

                """

           
                query = """
                    query SearchMostTop10Star($queryString: String!, $maybeAfter: String, $numberOfNodes: Int) {
                        search(query: $queryString, type: REPOSITORY, first: $numberOfNodes, after: $maybeAfter) {
                            edges {
                                node {
                                    ... on Repository {
                                        nameWithOwner
                                        url
                                        watchers {
                                            totalCount
                                        }
                                    }
                                }
                                cursor
                            }
                            repositoryCount
                        }
                    }
                    """

                language_filter = f"language:{language}" if language else ''
                stars_filter = f"stars:>{stars}" if stars else ''
                owner_filter = f"user:{owner}" if owner else ''
                date_range_filter = f"pushed: {date_range_str}" if date_range_str else ''
                
                variables = {
                    "queryString": ' '.join([language_filter, stars_filter, owner_filter, date_range_filter]),
                    "maybeAfter": cursor,
                    "numberOfNodes": GithubScraper._MAX_NODES_PER_LOOP
                }

                request = requests.post(GithubScraper._GITHUB_V4_URL,
                                    json={'query': query, 'variables': variables},
                                    headers=self.request_headers)

                result = request.json()

                if result['data']['search']['edges']:
                    # Get the next cursor
                    cursor = result['data']['search']['edges'][-1]['cursor']

                    # Yield nodes for each repo (generator pattern)
                    for edge in result['data']['search']['edges']:
                        yield edge['node']
                else:
                    # Processed all nodes
                    break

            except (ValueError, TypeError, KeyError) as exc:
                # pylint: disable=line-too-long
                self.logger.warning( f"Could not run query starting at {cursor} for {date_range_str}: {exc}: {result}")
                break

