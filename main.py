"""
Example of calling GitHub's Search Issue API

Script will find all the merged PRs contributed to a set of GitHub repositories for a given list of GitHub usernames.
Can use this to pull a list of contributions by individual and by team (where team is more than one individual)

Takes a simple config in the form of:

{
  "githubToken": "",   # GitHub access token to use
  "members": [
      # Comma separated list of GitHub usernames to query
      # If more than one, will provide "team" stats
  ],
  "range_start": "",  # Start date, find issues created *after* this date
  "range_end": "" # (Optional) end date for query, find issues created *before* this date
}

See GitHub documentation for more examples:
* https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests
* https://docs.github.com/en/search-github/getting-started-with-searching-on-github/understanding-the-search-syntax#query-for-dates

Pass the options -f <config.json> -o <github org> -r <results.csv> on start.
"""

import argparse
import csv
import json
import os
from pprint import pprint

import requests

BASE_API = 'https://api.github.com'


def search_issues_with_requests(query: str, token: str) -> []:
    """
    Call the GitHub Search Issues API with a given query and return
    all paginated results.

    :param query: The query to call against search issues API
    :param token: The GitHub personal access token
    :return: Array of each results
    """

    query_url = f'{BASE_API}/search/issues?q={query}'

    headers = {'Authorization': f'token {token}'}
    r = requests.get(query_url, headers=headers)
    results = r.json()['items']

    # Paginate and kee appending results
    while 'next' in r.links.keys():
        r = requests.get(r.links['next']['url'], headers=headers)
        results.extend(r.json()['items'])
    return results


def filter_item(item: {}, labels_to_filter=None) -> bool:
    """
    Filter out list of PRs based on passed set of excluded labels
    :param item: The GitHub PR to filter
    :param labels_to_filter: The labels to check for, if any match item is filtered
    :return: True if list filtered, false otherwise
    """
    if labels_to_filter is None:
        labels_to_filter = []

    _filtered = False

    if "labels" in item and len(labels_to_filter):
        labels = item['labels']

        if len(labels) != 0:
            for label in labels:
                if label['name'] in labels_to_filter:
                    _filtered = True
                    break

    return _filtered


def export_csv(csv_file: str, items: [], exclude_labels: []):
    with open(csv_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

        for item in items:
            if not filter_item(item=item, labels_to_filter=exclude_labels):
                title = item['title']
                repository_url = item['repository_url']
                url = item['url']
                csv_writer.writerow([title, url, repository_url])


def extract_prs(config: {}, organization: str) -> []:
    """
    Extract all submitted PRS in repositories owned by the passed organization
    :param config: The config file
    :param organization: The organization that owns rhe repositories in scope
    :return: All merged PRs
    """
    items_by_repro = {}
    prs_by_user = {}

    all_items = []
    range_end = config["range_end"] if config.get('range_end') else '*'

    _users = config['members']
    for user in _users:
        # User here is the org owner of the repositories to query
        query = f'author:{user}+is:pr+is:merged+user:{organization}+created:{config["range_start"]}..{range_end}'
        items = search_issues_with_requests(query=query, token=config["token"])

        print(f'{len(items)} merged PRs found for {user}')
        prs_by_user[user] = len(items)

        items_by_repro_by_user = {}
        for item in items:
            if not filter_item(item):
                title = item['title']
                repository_url = item['repository_url']
                url = item['url']

                # Print out PR title and URL.
                # Note: URL contains repository URL
                print(f'{title}\t{url}')

                # Accumulate per user
                if repository_url in items_by_repro_by_user:
                    count = items_by_repro_by_user[repository_url]
                    items_by_repro_by_user[repository_url] = count + 1
                else:
                    items_by_repro_by_user[repository_url] = 1

                # Accumulate for all users
                if repository_url in items_by_repro:
                    count = items_by_repro[repository_url]
                    items_by_repro[repository_url] = count + 1
                else:
                    items_by_repro[repository_url] = 1

        print(f"\n\nContributions by {user}:")
        pprint(items_by_repro_by_user)
        print(f"\t\tTotal: {len(items)}\n")
        all_items += items

    if len(_users) > 1:
        print("\n\nFor all members of the team:")
        pprint(items_by_repro)
        _total = 0
        print(f"\t\tTotal: {len(all_items)}\n")
    return all_items


def is_file(path: str) -> str:
    """
    Confirms if the given path is an actual file
    :param path: The path to check
    :return: The path if path exists, raises exception otherwise
    """
    if os.path.isfile(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"{path} is not file")


def is_new_file(path: str) -> str:
    """
    Confirms if the given path is valid for a new file
    :param path: The path to check
    :return: The path if path does not exist, raises exception otherwise
    """
    if not os.path.exists(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"{path} already exists")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pulls merged PRs for GitHub users on a team.')
    parser.add_argument('-filename', '-f', type=is_file, help="The config json to load")
    parser.add_argument('-organization', '-o', type=str, default='o3de',
                        help="The GitHub organization to check, defaults to O3DE")
    parser.add_argument('-result', '-r', type=is_new_file, help="[Optional] The results file, export all PRs as CSV")
    args = parser.parse_args()

    with open(args.filename, 'rt') as f:
        config = json.load(f)
        items = extract_prs(config=config, organization=args.organization)

        if args.result:
            print(f"Generating results csv: \"{args.filename}\"")

            exclude_labels = []
            if "exclude_labels" in config:
                exclude_labels = config["exclude_labels"]

            export_csv(csv_file=args.result, items=items, exclude_labels=exclude_labels)
