#!/bin/bash

# Read the GITHUB_TOKEN from the environment

if [ -z "$GITHUB_TOKEN" ]; then
  echo "The GITHUB_TOKEN is required."
  exit 1
fi

export GITHUB_TOKEN

pushd site
today=$(date  +'%Y-%m-%d')
# Execute the scripts in the keep directory: content will be versioned
for script in ../actions/keep/*; do
    # execute the script only if it is executable
    [ -x $script ] || continue
    find
    mkdir -p content/$(basename $script .sh)
    echo "Processing keep $script"
    $script nethserver nethesis > content/$(basename $script .sh)/$(basename $script .sh)_$today.md
done
# Execute scripts in the override directory: they will override the existing content
for script in ../actions/override/*; do
    # execute the script only if it is executable
    [ -x $script ] || continue
    find
    mkdir -p content/$(basename $script .sh)
    echo "Processing override $script"
    $script nethserver nethesis > content/$(basename $script .sh)/$(basename $script .sh).md
done
popd

