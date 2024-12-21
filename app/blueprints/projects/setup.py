"""Setup script for the projects blueprint."""

from setuptools import setup, find_packages

setup(
    name='flask-blackfridaylunch-projects',
    version='1.0.0',
    description='Project management blueprint for Flask Black Friday Lunch',
    author='Justin',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask>=2.0.0',
        'Flask-SQLAlchemy>=3.0.0',
        'Flask-Login>=0.6.0',
        'Flask-Migrate>=4.0.0',
        'Flask-WTF>=1.0.0',
        'SQLAlchemy>=2.0.0',
        'Werkzeug>=2.0.0',
        'Jinja2>=3.0.0',
        'WTForms>=3.0.0',
        'alembic>=1.0.0',
        'python-dateutil>=2.8.0'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
