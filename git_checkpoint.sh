#!/bin/bash

# Dream3D City Checkpoint Script

# Add all changes
echo "Adding files to git..."
git add .

# Prompt for a commit message if one isn't provided as an argument
if [ -z "$1" ]; then
    echo "Enter commit message (Press Enter for default: 'Chore: Refactor codebase structure and add CLI'):"
    read input_message
    if [ -z "$input_message" ]; then
        COMMIT_MSG="Chore: Refactor codebase structure and add CLI"
    else
        COMMIT_MSG="$input_message"
    fi
else
    COMMIT_MSG="$1"
fi

# Commit
echo "Committing with message: '$COMMIT_MSG'"
git commit -m "$COMMIT_MSG" -m "Details:
- Moved business logic to src/core
- Moved GUI code to src/gui
- Moved Go files to go/
- Added cli.py for command line usage
- Updated documentation in docs/
- Decoupled reconstruction and obj2gml logic from UI"

echo "Checkpoint created successfully!"
