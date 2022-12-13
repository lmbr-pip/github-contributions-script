"""
Code below provides examples of calling GitHub's Search Issue API

Script will find all the merged PRs contributed to a set of GitHub repositories for a given list of GitHub usernames. It
can optionally also find all the issues created.

Can use this to generate a list of contributions by an individual and by team (where team is more than one individual)

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

Use the example.json file as a starting point.

To work with GitHub's search api see the following GitHub documentation for more examples:
* https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests
* https://docs.github.com/en/search-github/getting-started-with-searching-on-github/understanding-the-search-syntax#query-for-dates


Pass the options -f <example.json> -o <github org> -r <results.csv> on start.
"""

import argparse
import csv
import json
import os
from pprint import pprint

from ghi_searcher import GitHubIssuesSearcher


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


def export_csv(csv_file: str, export_items: [], labels_to_exclude: []):
    """
    Export list of GitHub issue items to a CSV file
    :param csv_file: The file to write results to
    :param export_items: The list of items to export
    :param labels_to_exclude: If provided, any items with a label match will be excluded
    """
    with open(csv_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)

        for item in export_items:
            if not filter_item(item=item, labels_to_filter=labels_to_exclude):
                title = item['title']
                repository_url = item['repository_url']
                url = item['url']
                csv_writer.writerow([title, url, repository_url])


def extract_issues(settings_config: {}, organization: str, extract_prs: bool = True) -> []:
    """
    Extract all submitted PRS or created issues in repositories owned by the passed organization
    :param settings_config: The config settings
    :param organization: The organization that owns rhe repositories in scope
    :param extract_prs: If true extract PRs, if false extract created issues
    :return: All contributions (either PRs or Issues)
    """
    items_by_repro = {}
    prs_by_user = {}

    all_items = []
    range_end = settings_config["range_end"] if settings_config.get('range_end') else '*'

    _token = settings_config.get("github_token")
    _users = settings_config['members']

    issue_searcher = GitHubIssuesSearcher(access_token=_token)

    for user in _users:
        # User here is the org owner of the repositories to query
        if extract_prs:
            # Extract merged PRs
            _query = issue_searcher.pr_ranged_merged_query(user=user,
                                                           organization=organization,
                                                           range_start=settings_config['range_start'],
                                                           range_end=range_end)
        else:
            # Extract opened issues
            _query = issue_searcher.issue_ranged_opened_query(user=user,
                                                              organization=organization,
                                                              range_start=settings_config['range_start'],
                                                              range_end=range_end)
        _items = issue_searcher.search_issues_with_requests(query=_query)

        _type = 'merged PRs' if extract_prs else 'opened issues'
        print(f'{len(_items)} {_type} found for {user}')

        prs_by_user[user] = len(_items)

        # Group items by user, by team and repository to measure overall contributions
        items_by_repro_by_user = {}
        for item in _items:
            if not filter_item(item):
                title = item['title']
                repository_url = item['repository_url']
                url = item['url']
                pr_number = item['number']

                # Print out number, title and URL (contains repository URL)
                print(f'[{pr_number}]\t{title}\t{url}')

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
        print(f"\t\tTotal: {len(_items)}\n")
        all_items += _items

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
    parser = argparse.ArgumentParser(
        description='Helper utils to extract either merged PRs or created issues for GitHub users on a team.')
    parser.add_argument('-filename', '-f', required=True, type=is_file, help="The config json to load")
    parser.add_argument('-organization', '-o', type=str, default='o3de',
                        help="The GitHub organization to check, defaults to O3DE")
    parser.add_argument('-issues', '-i', action='store_true', help='If provided searches issues rather than PRs')
    parser.add_argument('-result', '-r', type=is_new_file, help="The results file, export all results in as CSV")
    args = parser.parse_args()

    with open(args.filename, 'rt') as f:
        config = json.load(f)
        _ps = not args.issues
        items = extract_issues(settings_config=config, organization=args.organization, extract_prs=_ps)

        if args.result:
            print(f"Generating results csv: \"{args.filename}\"")

            exclude_labels = []
            if "exclude_labels" in config:
                exclude_labels = config["exclude_labels"]

            export_csv(csv_file=args.result, export_items=items, labels_to_exclude=exclude_labels)
