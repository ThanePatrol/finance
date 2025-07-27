#!/usr/bin/env bash

# This script provides a convenient way to run the budget/main.py script
# using the Nix development shell defined in flake.nix.

# Exit immediately if a command exits with a non-zero status.
set -e

# Get the absolute path of the project root directory (where the script is located).
# This ensures the script can be run from any directory.
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Change to the project root directory. This is crucial so that the shellHook
# in flake.nix can find the .venv and .env files.
cd "$SCRIPT_DIR"

echo "Executing budget/main.py inside the Nix development shell..."

# Use 'nix develop' to run the python script in the development shell.
# The flake URI ".#" points to the flake in the current directory.
# The shellHook defined in flake.nix handles activating the virtual environment
# and exporting environment variables from the .env file.
# "$@" passes all arguments from this script to the python script.
nix develop .# --command python budget/main.py "$@"

echo "Script execution finished."
