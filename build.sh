#!/usr/bin/env bash
# Render build script for backend

set -o errexit

echo "=== Checking Python Version ==="
python --version
python3 --version || true

# Verify we're using Python 3.11
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
if [[ ! $PYTHON_VERSION =~ ^3\.11\. ]]; then
    echo "ERROR: Expected Python 3.11.x, got $PYTHON_VERSION"
    echo "Make sure runtime.txt is set to python-3.11.9"
    exit 1
fi

echo "=== Installing dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Running database setup ==="
python create_admin.py

echo "=== Build completed successfully! ==="
