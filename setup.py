from setuptools import setup, find_packages
import os

def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(req_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='gitmedic',
    version='1.0',
    author='Simone Laganà',
    author_email='simone.lagana12@gmail.com',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'gitmedic=backend.cli:main',
        ],
    },
    python_requires='>=3.9',
)
