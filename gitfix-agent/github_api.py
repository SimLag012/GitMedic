import os
from github import Github
from config import setup_config

setup_config()

def search_issues():
    """
    Searches for an open issue with the 'bug' label on Python.
    The refined query is: "is:issue is:open label:bug language:python"
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN not found.")
        return None
        
    g = Github(token)
    
    # Execute the query filtering by size (< 5MB)
    query = "is:issue is:open label:bug language:python size:<5000"
    issues = g.search_issues(query)
    
    if issues.totalCount == 0:
        print("No issues found.")
        return None
        
    # Take the first available issue
    issue = issues[0]
    
    return {
        "repo_name": issue.repository.full_name,
        "repo_url": issue.repository.clone_url,
        "issue_id": issue.number,
        "title": issue.title,
        "description": issue.body
    }
