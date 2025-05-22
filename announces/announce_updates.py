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
import json

def translate_announcement_prompt(announcement, language):
    """Create a prompt for the LLM to translate the announcement."""
    return ChatPromptTemplate.from_messages([
        ("system", f"You are a professional translator."),
        ("user", f"Translate the following announcement into {language}. Keep markdown formatting and do not change the meaning.\n\n{announcement}.")
   ])

def translate_announcement_title_prompt(title, language):
    """Create a prompt for the LLM to translate the title."""
    return ChatPromptTemplate.from_messages([
        ("system", f"You are a professional translator."),
        ("user", f"Translate the following title into {language}. Keep markdown formatting and do not change the meaning.\n\n{title}.")
   ])

def create_announcement_title(product):
    """Create a prompt for the LLM to generate a title for the announcement."""
    return ChatPromptTemplate.from_messages([
        ("system", f"""You are an expert in communication, to explain techincal things to non-techincal peopole.
        Your goal is to create a title that summarizes the list of changes.
        This is not a full release, but just a summary of recent changes.
        You can use emoticons but not bold or italic.
        Write in English"""),
        ("user", f"""Create a title for the following announcement for product {product}.
        The post will be sent to Discourse community.
        Keep it brief and clear, ensuring it's understandable to a technical audience unfamiliar with the codebase.
        Each product should have different titles and emoticons. Use no more than one emoticon. Use these emoticons:
         - NethServer: something related to containers or packages
         - NethSecurity: something related to security, shield, wall or firewall
         - NethVoice: something related to telephony or voice
         - Anything else: you choose
        """)
    ])

def create_announcement_prompt(product, issues):
	"""Create a prompt for the LLM to generate the announcement."""
	return ChatPromptTemplate.from_messages([
		("system", f"""You are an expert in simplifying technical release notes for broader audiences.
		Your goal is to explain complex release notes, focusing on clarity and relevance for community users
        without deep technical knowledge. This is not a full release, but just a summary of recent changes.
        You're given a list of issues already explained.
        Organize them for a release announcement.
        First, explain the features than list the bug fixes.
        Try to highlight the most important features and bug fixes.
        Do not invent any information.
		Write in English"""),
		("user", f"""Create a 2-week summary for the following product {product}.
        Use a professional style and a friendly tone.
        The summary should be suitable for a community audience.
        Focus on the most important features and bug fixes.
        The post will be sent to Discourse community forum so make sure to use markdown formatting. 
		Keep it brief and clear, ensuring it's understandable to a technical audience unfamiliar with the codebase.
        If an issue is a Design type, highlight that a mockup is available but the feature is not implemented yet.
   
        Each product should have different titles and emoticons. Use no more than one emoticon. Use these emoticons:
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
    parser.add_argument("--config-file", required=True, help="Path to the configuration file (required).")
    args = parser.parse_args()

    # Get environment variable for GitHub token
    gh_token = os.getenv("GITHUB_TOKEN")
    if not gh_token:
        print("Error: GITHUB_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    # Check if the script is running on GitHub CI
    if os.getenv("CI") is not None:
        wait_time = random.randint(5, 60)
        print(f"Running on GitHub CI. Waiting for {wait_time} seconds to avoid rate limits.", file=sys.stderr)
        time.sleep(wait_time)

    # Get the date from two weeks ago in ISO format
    two_weeks_ago = (datetime.now(timezone.utc) - timedelta(days=14)).replace(hour=0, minute=0, second=1, microsecond=0).isoformat()

    # Create the LLM chain
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=gh_token,
        base_url="https://models.inference.ai.azure.com",
    )

    # Load the configuration file
    with open(args.config_file, "r") as fp:
        config = json.load(fp)

    to_be_published = []

    # Generate the announcement for each product
    for product in config["products"]:
        print(f"Processing product: {product.get('name')}", file=sys.stderr)
        closed_issues = fetch_closed_issues(gh_token, product.get('name'), product.get('repository'), two_weeks_ago)

        if not closed_issues:
            print(f"Skipping {product.get('name')}: no closed issues", file=sys.stderr)
        else:
            changes = create_change_list(closed_issues)  

            # Generate the English announcement
            response_en = llm.invoke(create_announcement_prompt(product.get('name'), changes).format_prompt())
            announcement_en = response_en.content
            title_en = llm.invoke(create_announcement_title(product.get('name')).format_prompt()).content

            if not announcement_en.strip() or not title_en.strip():
                print("Error on English announcement: content or title is empty.", file=sys.stderr)
            else:
                print(f"Writing announcement to file: announcement-{product.get('name')}-en.md", file=sys.stderr)
                with open(f"announcement-{product.get('name')}-en.md", "w") as f:
                    f.write(announcement_en)
                to_be_published.append( {"language": "english", "title": title_en, "content": announcement_en} )
                
            response_it = llm.invoke(translate_announcement_prompt(announcement_en, "Italian").format_prompt())
            announcement_it = response_it.content
            title_it = llm.invoke(translate_announcement_title_prompt(title_en, "Italian").format_prompt()).content

            if not announcement_it.strip() or not title_it.strip():
                print("Error on Italian announcement: content or title is empty.", file=sys.stderr)
            else:
                print(f"Writing announcement to file: announcement-{product.get('name')}-it.md", file=sys.stderr)
                with open(f"announcement-{product.get('name')}-it.md", "w") as f:
                    f.write(announcement_it)
                to_be_published.append( {"language": "italian", "title": title_it, "content": announcement_it} )
            
            break

    # Send to Discourse
    for draft in to_be_published:
        discourse_config = config["discourses"][draft["language"]]
        headers = {"Accept": "application/json; charset=utf-8", "Api-Username": discourse_config["api_username"], "Api-Key": discourse_config["api_key"]}

        tmp = {"raw": draft['content'], "category": discourse_config.get("category_id"), "title": draft["title"], "tags": discourse_config.get('tags')}
        print(f"Sending to Discourse: {tmp}", file=sys.stderr)
        continue
        discourse_response = requests.post(
            f'{args.discourse_host}/posts',
            json={"raw": draft['content'], "category": discourse_config.get("category_id"), "title": draft["title"], "tags": discourse_config.get('tags')},
            headers=headers,
            allow_redirects=True
        )
        if discourse_response.status_code == 200:
            print("Message sent to Discourse!", file=sys.stderr)
        else:
            print(f"Discourse response: {discourse_response.json()}", file=sys.stderr)
            print(f"Error when sending the message to Discourse: {discourse_response.text}", file=sys.stderr)
            sys.exit(1)
