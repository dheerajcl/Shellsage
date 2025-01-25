from setuptools import setup, find_packages

setup(
    name='error_assistant',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'requests>=2.31.0',  # Specify version
        'click>=8.1.0',
    ],
    entry_points={
        'console_scripts': [
            'error-assist=error_assistant.cli:main',
        ],
    },
)