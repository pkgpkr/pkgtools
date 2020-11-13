import logging
FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATEFMT = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(format=FORMAT, datefmt=DATEFMT, level=logging.INFO)

from .github_scraper import GithubScraper