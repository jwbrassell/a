import os
import fileinput
import sys

def fix_imports(directory):
    """Replace 'from app import db' with 'from app.extensions import db' in all Python files."""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with fileinput.FileInput(filepath, inplace=True) as file:
                    for line in file:
                        if line.strip() == 'from app import db':
                            print('from app.extensions import db')
                        elif line.strip() == 'from app import db, create_app':
                            print('from app.extensions import db\nfrom app import create_app')
                        else:
                            print(line, end='')

if __name__ == '__main__':
    fix_imports('app')
