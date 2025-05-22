# Announces

This directory contains scripts for announcing new releases.

## announce_updates.py

`announce_updates.py` is a script designed to automate the process of announcing updates every 2 weeks. 
It gathers relevant information about recent changes, compiles it into a structured format, and prepares it for distribution to the intended audience.
The scripts creates announcements for the following products:
- NethServer
- NethSecurity
- NethVoice

Each announcement is generated in English and Italian.
English announcements are sent to the https://community.nethserver.org/ forum, while Italian announcements are sent to the https://forum.nethserver.it/ forum.


Usage example for NethSecurity:
```
GITHUB_TOKEN=$(gh auth token) ./announce_updates.py --config config.json
```

Example of a config file:
```json
{
    "products": [
        { "name": "NethSecurity", "repository": "nethserver/nethsecurity", "tags": ["nethsecurity"] },
        { "name": "NethVoice", "repository": "nethserver/dev", "tags": ["nethvoice"] },
        { "name": "NethServer", "repository": "nethserver/dev", "tags": ["ns8"] }
    ],
    "discourses": {
        "english": { "api_key": "xxx", "api_username": "nethbot", "category_id": 24, "host": "https://community.nethserver.org" },
        "italian": { "api_key": "xxx", "api_username": "nethbot", "category_id": 14, "host": "https://partner.nethesis.it" }
    }
}
```

Explanation of the config file:
- `products`: A list of products to be announced. Each product has a name, a GitHub repository, and a list of tags.
  - `name`: The name of the product (e.g., NethSecurity, NethVoice, NethServer), it must match the first part of milestone names.
  - `repository`: The GitHub repository of the issue tracker for the product (e.g., nethserver/nethsecurity).
  - `tags`: A list of tags associated with the product (e.g., ["nethsecurity"]).

- `discourses`: A dictionary containing the configuration for the two discourse forums (English and Italian).
    - `english`: Configuration for the English discourse forum.
        - `api_key`: The API key for authentication.
        - `api_username`: The username of the bot used to post announcements.
        - `category_id`: The ID of the category where announcements will be posted.
        - `host`: The URL of the English discourse forum.
    
    - `italian`: Configuration for the Italian discourse forum, with the same structure as the English configuration.