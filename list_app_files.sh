#!/bin/bash

# Find all files in app directory
# Exclude static directory and any logs directories
# Sort the output
find app \
    -type f \
    ! -path "*/static/*" \
    ! -path "*/logs/*" \
    ! -path "*.pyc" \
    ! -path "*/__pycache__/*" \
    | sort
