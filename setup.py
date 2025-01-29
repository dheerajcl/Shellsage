from setuptools import setup, find_packages

setup(
    name='shellsage',
    version='1.0.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'click>=8.1.0',
        'requests>=2.31.0',
        'openai>=1.12.0',
        'pyyaml>=6.0.1',
        'inquirer>=3.1.3',
        'ctransformers>=0.2.27',
        'python-dotenv>=1.0.0'
    ],
    entry_points={
        'console_scripts': [
            'shellsage=shellsage.cli:cli',
        ],
    },
    include_package_data=True,
)