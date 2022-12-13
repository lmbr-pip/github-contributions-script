import requests


class GitHubResponses:
    OK = 200
    ACCEPTED = 202
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    REQUEST_FORBIDDEN = 403
    NOT_FOUND = 404
    VALIDATION_FAILED = 422
    SERVER_ERROR = 500


class HttpUnauthorizedError(Exception):
    pass


class HttpBadRequestError(Exception):
    pass


class HttpInternalServerError(Exception):
    pass


class GitHubRequests(object):
    """
    General functionality to make GHI API requests easier to work with
    See https://docs.github.com/en/rest for API details
    """

    BASE_API = 'https://api.github.com'

    def __init__(self, access_token: str):
        """
        :param access_token: GitHub access token for automation.
        """
        self._token = access_token

    @staticmethod
    def _validate(response: requests.Response) -> {}:
        if response.status_code == GitHubResponses.UNAUTHORIZED:
            raise HttpUnauthorizedError('Not authorized, check your github access token in \"githubToken\"')
        elif response.status_code == GitHubResponses.SERVER_ERROR:
            raise HttpInternalServerError('GitHub internal server error, try again or check GitHub status page')
        elif response.status_code == GitHubResponses.OK or response.status_code == GitHubResponses.ACCEPTED:
            print('200 Response from Github - extracting information')
            return response.json()
        else:
            raise HttpBadRequestError(
                f'Something went wrong calling. Call failed with status code: {response.status_code} '
                f'- {response.reason}. \n Full Response was: \"{str(response)}\"')

    def execute_query(self, api_path: str, query: str) -> {}:
        """
        Call the GitHub Search Issues API with a given query and return
        all paginated results
        :param api_path: The GitHub API to call
        :param query: The query to call against search issues API
        :return: Array of each results
        """
        query_url = f'{GitHubRequests.BASE_API}/{api_path}?q={query}'

        headers = {'Authorization': f'token {self._token}'}
        r = requests.get(query_url, headers=headers)

        return GitHubRequests._validate(r)

    def execute_and_page(self, api_path: str, query: str, key: str) -> []:
        query_url = f'{GitHubRequests.BASE_API}/{api_path}?q={query}'

        headers = {'Authorization': f'token {self._token}'}
        r = requests.get(query_url, headers=headers)

        results = GitHubRequests._validate(r)[key]

        # Paginate and keep appending results
        while 'next' in r.links.keys():
            r = requests.get(r.links['next']['url'], headers=headers)
            results.extend(r.json()[key])
        return results
