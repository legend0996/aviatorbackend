#!/usr/bin/env bash
# Render build script for backend

set -o errexit

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Running database setup..."
python create_admin.py

echo "Build completed successfully!"
