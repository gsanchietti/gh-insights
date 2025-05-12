#!/usr/bin/python3

#
# SPDX-License-Identifier: GPL-3.0-or-later
#

# This script fetches closed issues from a GitHub repository and sends an announcement to Discourse

import os
import sys
import requests
from datetime import datetime, timezone, timedelta
import ghexplain
import argparse
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import random
import time


def create_announcement_title(product, language):
    """Create a prompt for the LLM to generate a title for the announcement."""
    return ChatPromptTemplate.from_messages([
        ("system", f"""You are an expert in creating titles for release notes.
        Your goal is to create a title that summarizes the release notes.
        You can use emoticons but not bold or italic.
        Write in {language}"""),
        ("user", f"""Create a title for the following announcement for product {product}.
        The post will be sent to Discourse community.
        Keep it brief and clear, ensuring it's understandable to a technical audience unfamiliar with the codebase.
        Each product should have different titles and emoticons. Use these emoticons:
         - NethServer: something related to containers or packages
         - NethSecurity: something related to security, shield, wall or firewall
         - NethVoice: something related to telephony or voice
         - Anything else: you choose
        """)
    ])

def create_announcement_prompt(product, issues, language):
	"""Create a prompt for the LLM to generate the announcement."""
	return ChatPromptTemplate.from_messages([
		("system", f"""You are an expert in simplifying technical release notes for broader audiences.
		Your goal is to explain complex release notes, focusing on clarity and relevance for community users
        without deep technical knowledge.
        You're given a list of issues already explained.
        Organize them for a release announcement.
        First, explain the features than list the bug fixes.
        Try to highlight the most important features and bug fixes.
        Do not invent any information.
		Write in {language}"""),
		("user", f"""Create a 2-week summary for the following product {product}.
        Use a professional style and a friendly tone.
        The summary should be suitable for a community audience.
        Focus on the most important features and bug fixes.
        The post will be sent to Discourse community forum so make sure to use markdown formatting. 
		Keep it brief and clear, ensuring it's understandable to a technical audience unfamiliar with the codebase.
        If an issue is a Design type, highlight that a mockup is available but the feature is not implemented yet.
   
        Each product should have different titles and emoticons. Use these emoticons:
         - NethServer: something related to containers or packages
         - NethSecurity: something related to security, shield, wall or firewall
         - NethVoice: something related to telephony or voice
         - Anything else: you choose
   
        Here's the list of changes:
        {issues}
		""")
	])

def fetch_closed_issues(token, product, repository, since):
    issues = []
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(f"https://api.github.com/repos/{repository}/issues", headers=headers, params={"state": "closed", "since": since, "per_page": 100})
    response.raise_for_status()
    for issue in response.json():
        # skip pull requests
        if 'pull_request' in issue:
            continue
        # skip issues whose milestone title does not match the product (case insensitive match at the start)
        if issue.get('milestone') and not issue['milestone']['title'].lower().startswith(product.lower()):
            print(f"Skipping issue {issue['number']} with milestone title {issue['milestone']['title']}", file=sys.stderr)
            continue
        # skip not planned issues
        if issue.get('state_reason') != "completed":
            print(f"Skipping issue {issue['number']} with state reason {issue['state_reason']}", file=sys.stderr)
            continue
        issues.append(issue)

    return issues

def create_change_list(issues):
    announcement = f"## Released updates\n\n"
    for issue in issues:
        # log to stderr the processed issue
        print(f"Processing issue {issue['number']}: {issue["title"]}", file=sys.stderr)
        icon = ""
        title = issue["title"]
        url = issue["html_url"]
        if any('milestone goal' in label['name'] for label in issue['labels']):
            icon = f"{title} :crown:"  # Highlight the title
        announcement += f"#### {title} ([{issue['number']}]({url})) {icon}\n"
        try:
            explanation = ghexplain.issue(url)
        except Exception as e:
            print(f"[ERROR] Skipping issue {issue['number']} due to error: {e}", file=sys.stderr)
            continue
        announcement += f"{explanation}\n"
        if 'type' in issue and issue['type']:
            announcement += f"Issue type: {issue['type']['name']}\n"
        if icon:
            announcement += "\nThis feature is a milestone goal.\n\n"
    return announcement

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Announce weekly updates.")
    parser.add_argument("--discourse-host", required=True, help="Discourse host (required).")
    parser.add_argument("--discourse-category-id", required=True, type=int, help="Discourse category ID (required).")
    parser.add_argument("--discourse-tags", type=lambda s: s.split(','), help="Optional comma-separated list of tags for the Discourse post.")
    parser.add_argument("--github-repository", required=True, help="Repository in the form Organization/repository (required).")
    parser.add_argument("--product", required=True, help="Product name (required).")
    parser.add_argument("--language", default="english", help="Language for the announcement (default: english).")
    args = parser.parse_args()

    # Get environment variable for GitHub token
    gh_token = os.getenv("GITHUB_TOKEN")
    if not gh_token:
        print("Error: GITHUB_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    # Get environment variable for Discourse API username
    discourse_api_username = os.getenv("DISCOURSE_API_USERNAME")
    if not discourse_api_username:
        print("Error: DISCOURSE_API_USERNAME environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    # Get environment variable for Discourse API key
    discourse_api_key = os.getenv("DISCOURSE_API_KEY")
    if not discourse_api_key:
        print("Error: DISCOURSE_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    # Check if the script is running on GitHub CI
    if os.getenv("CI") is not None:
        wait_time = random.randint(5, 60)
        print(f"Running on GitHub CI. Waiting for {wait_time} seconds to avoid rate limits.", file=sys.stderr)
        time.sleep(wait_time)

    # Get the date from two weeks ago in ISO format
    two_weeks_ago = (datetime.now(timezone.utc) - timedelta(days=14)).replace(hour=0, minute=0, second=1, microsecond=0).isoformat()

    closed_issues = fetch_closed_issues(gh_token, args.product, args.github_repository, two_weeks_ago)
    if not closed_issues:
        print("No updates", file=sys.stderr)
        sys.exit(0)
    changes = create_change_list(closed_issues)  

    # Create the LLM chain
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=gh_token,
        base_url="https://models.inference.ai.azure.com",
        #rate_limiter=rate_limiter
    )

	# Generate the announcement
    response = llm.invoke(create_announcement_prompt(args.product, changes, args.language).format_prompt())
    announcement = response.content
    title = llm.invoke(create_announcement_title(args.product, args.language).format_prompt()).content

    # Exit if announcement or title are empty
    if not announcement.strip() or not title.strip():
        print("Error: Announcement or title is empty.", file=sys.stderr)
        sys.exit(1)

    # Output the announcement to a file for later use
    file = f"announcement-{args.product}-{args.language}.md"
    print(f"Writing announcement to {file}", file=sys.stderr)
    with open(file, "w") as f:
        f.write(announcement)

    # Send to Discourse
    headers = {"Accept": "application/json; charset=utf-8", "Api-Username": discourse_api_username, "Api-Key": discourse_api_key}
    discourse_response = requests.post(
        f'{args.discourse_host}/posts',
        json={"raw": announcement, "category": args.discourse_category_id, "title": title, "tags": args.discourse_tags},
        headers=headers,
        allow_redirects=True
    )
    if discourse_response.status_code == 200:
        print("Message sent to Discourse!", file=sys.stderr)
    else:
        print(f"Discourse response: {discourse_response.json()}", file=sys.stderr)
        print(f"Error when sending the message to Discourse: {discourse_response.text}", file=sys.stderr)
        sys.exit(1)