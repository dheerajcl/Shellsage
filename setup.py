from setuptools import setup, find_packages

setup(
    name='shellsage',
    version='1.0.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'click>=8.1.0',
        'requests>=2.31.0'
    ],
    entry_points={
        'console_scripts': [
            'shellsage=error_assistant.cli:cli',
        ],
    },
)