from setuptools import setup, find_packages
import os

# Read requirements from requirements.txt
def read_requirements():
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='gitmedic',
    version='1.0',
    author='Simone Laganà',
    author_email='simone.lagana12@gmail.com', 
    packages=find_packages(),
    py_modules=['run', 'agent', 'llm', 'tester', 'blockchain', 'github_api', 'config'],
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'gitmedic=run:main',
        ],
    },
)
