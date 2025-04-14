# Announces

This directory contains scripts for announcing new releases.

## announce_updates.py

`announce_updates.py` is a script designed to automate the process of announcing updates every 2 weeks. 
It gathers relevant information about recent changes, compiles it into a structured format, and prepares it for distribution to the intended audience.

Usage example for NethSecurity:
```
DISCOURSE_API_USERNAME=test DISCOURSE_API_KEY=test GITHUB_TOKEN=$(gh auth token) ./announce_updates.py --discourse-host http://localhost --discourse-category-id 1 --github-repository NethServer/nethsecurity --product NethSecurity --language English
```

Usage example for NethVoice:
```
DISCOURSE_API_USERNAME=test DISCOURSE_API_KEY=test GITHUB_TOKEN=$(gh auth token) ./announce_updates.py --discourse-host http://localhost --discourse-category-id 1 --github-repository NethServer/dev --product NethVoice --language English
```

Usage example for NethServer:
```
DISCOURSE_API_USERNAME=test DISCOURSE_API_KEY=test GITHUB_TOKEN=$(gh auth token) ./announce_updates.py --discourse-host http://localhost --discourse-category-id 1 --github-repository NethServer/dev --product NethServer --language English
```