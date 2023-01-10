from ghi_requests import GitHubRequests


class GitHubIssuesSearcher(object):
    """
    Helper class to make working with GitHub's search/issues API (https://docs.github.com/en/rest/search) easier.

    See https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests for help
    with query syntax
    """

    QUERY_PATH = 'search/issues'

    def __init__(self, access_token: str):
        self._token = access_token

    def pr_ranged_merged_query(self, user: str, organization: str, range_start: str, range_end: str) -> str:
        """
        Builds a query to find all the merged PRs by the user in the provided date range
        :param user: the GitHub user id
        :param organization: matches issues in repositories owned by the GitHub organization
        :param range_start: The starting date range
        :param range_end: (Optional) the ending date range
        :return: query to use with search api
        """
        return f'author:{user}+is:pr+is:merged+user:{organization}+created:{range_start}..{range_end}'

    def pr_ranged_reviewed_query(self, user: str, organization: str, range_start: str, range_end: str) -> str:
        """
        Builds a query to find all the reviewed PRs by the user in the provided date range
        :param user: the GitHub user id
        :param organization: matches issues in repositories owned by the GitHub organization
        :param range_start: The starting date range
        :param range_end: (Optional) the ending date range
        :return: query to use with search api
        """
        return f'is:pr+reviewed-by:{user}+user:{organization}+created:{range_start}..{range_end}'

    def issue_ranged_closed_query(self, user: str, organization: str, range_start: str, range_end: str) -> str:
        """
        Find all the closed issues created by the user in given range
        Note: Does not find all the issues closed by the user
        :param user: the GitHub user id
        :param organization: matches issues in repositories owned by the GitHub organization
        :param range_start: The starting date range
        :param range_end: (Optional) the ending date range
        :return: query to use with search api
        """
        return f'author:{user}+is:issue+is:closed+user:{organization}+created:{range_start}..{range_end}'

    def issue_ranged_opened_query(self, user: str, organization: str, range_start: str, range_end: str) -> str:
        """
        Find all the issues created by the user in given range
        :param user: the GitHub user id
        :param organization: matches issues in repositories owned by the GitHub organization
        :param range_start: The starting date range
        :param range_end: (Optional) the ending date range
        :return: query to use with search api
        """
        return f'author:{user}+is:issue+user:{organization}+created:{range_start}..{range_end}'

    def search_issues_with_requests(self, query: str) -> []:
        """
        Call the GitHub Search Issues API with a given query and return
        all paginated results
        :param query: The query to call against search issues API
        :return: Array of each results
        """
        requestor = GitHubRequests(self._token)
        return requestor.execute_and_page(api_path=GitHubIssuesSearcher.QUERY_PATH, query=query, key='items')
