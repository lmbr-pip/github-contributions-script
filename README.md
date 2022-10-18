# Overview

An example of calling GitHub's Search Issue API to pull contributions for a given list of contributors

Exports list of merged PRs as a CSV file.

## Getting Started

### Create a config file
```
{
  "githubToken": "",   # This should be your GitHub access token
  "members": [
      # Comma separated list of GitHub usernames to query
  ],
  "repositories": [
     # List of repostiries to include ie "o3de/o3de"
  ],
  "range_start": "",  # Start date, find issues created *after* this date
  "range_end": "" # (Optional) end date for query, find issues created *before* this date
}
```
### Run the Script
Will take a config file and find all the merged PRs in the 'O3DE' set of repositories.

Results will be outputted to results.csv

```
python main.py -f config.json -o 'O3DE' -r <esults.csv
```

## More Information 

* https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests
* https://docs.github.com/en/search-github/getting-started-with-searching-on-github/understanding-the-search-syntax#query-for-dates