#!/bin/bash

# Read the GITHUB_TOKEN from the environment

if [ -z "$GITHUB_TOKEN" ]; then
  echo "The GITHUB_TOKEN is required."
  exit 1
fi

export GITHUB_TOKEN

pushd site
today=$(date  +'%Y-%m-%d')
for script in ../actions/*; do
    mkdir -p content/$(basename $script .sh)
    echo "Processing $script"
    $script nethserver nethesis > content/$(basename $script .sh)/$(basename $script .sh)_$today.md
done
popd

