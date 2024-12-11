import os
import re
import shutil

def find_and_replace(directory):
    # First check if we need to rename the directory itself
    if 'blackfriday' in directory.lower():
        print(f"\n=== Current Directory Contains 'blackfriday' ===")
        print(f"Current path: {directory}")
        new_name = os.path.basename(directory).replace('blackfriday', 'squirrel')
        print(f"Would be renamed to: {new_name}")
        response = input("\nWould you like to rename the directory? (y/n): ")
        if response.lower() == 'y':
            parent_dir = os.path.dirname(directory)
            new_path = os.path.join(parent_dir, new_name)
            os.rename(directory, new_path)
            directory = new_path
            print(f"✓ Directory renamed to: {new_path}")

    # First pass: Check markdown files
    print("\n=== Checking Documentation Files (.md) ===")
    for root, dirs, files in os.walk(directory):
        for file in files:
            if not file.endswith('.md'):
                continue
                
            filepath = os.path.join(root, file)
            check_and_replace_file(filepath)
    
    # Second pass: Check all other files
    print("\n=== Checking All Other Files ===")
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                continue
                
            filepath = os.path.join(root, file)
            # Skip certain file types and directories
            if any(skip in filepath for skip in ['.git', '__pycache__', '.pyc', '.env', '.log']):
                continue
                
            check_and_replace_file(filepath)

def check_and_replace_file(filepath):
    try:
        # Try to read the file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # If "blackfriday" is found in the content
        if 'blackfriday' in content.lower():
            print(f"\nFound matches in: {filepath}")
            print("-" * 50)
            
            # Find and print lines containing "blackfriday"
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'blackfriday' in line.lower():
                    print(f"Line {i+1}: {line.strip()}")
            
            # Ask for confirmation before replacing
            response = input("\nReplace 'blackfriday' with 'squirrel' in this file? (y/n): ")
            if response.lower() == 'y':
                # Replace the text (case-insensitive)
                new_content = re.sub('blackfriday', 'squirrel', content, flags=re.IGNORECASE)
                
                # Write the changes back to the file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✓ Changes applied to {filepath}")
            else:
                print("× Skipped file")
            print("-" * 50)
                
    except (UnicodeDecodeError, IOError):
        # Skip files that can't be read as text
        pass

if __name__ == "__main__":
    current_dir = os.getcwd()
    print(f"Starting search in: {current_dir}")
    print("Note: Ignoring .git, __pycache__, .pyc, .env, and .log files")
    find_and_replace(current_dir)
    print("\nSearch complete!")
