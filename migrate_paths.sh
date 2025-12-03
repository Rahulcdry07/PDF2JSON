#!/bin/bash
#
# Migration Script: Update paths from old to new structure
#
# This script updates file paths in the codebase to match the new
# organized directory structure.
#

set -e

PROJECT_ROOT="/Users/rahulchaudhary/PDF2JSON"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "PDF2JSON - Path Migration Script"
echo "=========================================="
echo ""

# Create symlinks for backward compatibility
echo "Creating backward-compatible symlinks..."

# Symlink old directories to new data/ structure
if [ ! -L "reference_files" ]; then
    ln -s data/reference reference_files
    echo "✓ Created symlink: reference_files -> data/reference"
fi

if [ ! -L "examples" ]; then
    ln -s data/examples examples
    echo "✓ Created symlink: examples -> data/examples"
fi

if [ ! -L "uploads" ]; then
    ln -s data/uploads uploads
    echo "✓ Created symlink: uploads -> data/uploads"
fi

if [ ! -L "backups" ]; then
    ln -s data/backups backups
    echo "✓ Created symlink: backups -> data/backups"
fi

if [ ! -L "logs" ]; then
    ln -s data/logs logs
    echo "✓ Created symlink: logs -> data/logs"
fi

if [ ! -L ".env.example" ]; then
    ln -s config/env.example .env.example
    echo "✓ Created symlink: .env.example -> config/env.example"
fi

echo ""
echo "✓ Backward compatibility symlinks created"
echo ""
echo "The project now uses the new structure:"
echo "  - All docs in docs/"
echo "  - All data in data/"
echo "  - All config in config/"
echo ""
echo "Old paths still work via symlinks!"
echo ""
echo "=========================================="
