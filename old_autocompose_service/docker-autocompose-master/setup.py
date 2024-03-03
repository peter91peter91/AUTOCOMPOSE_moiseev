from setuptools import setup, find_packages
setup(
    name = "docker-autocompose",
    version = "1.1",
    description = "Generate a docker-compose yaml definition from a running container",
    url = "https://github.com/peter91peter91/docker-autocompose",
    author = "Red5d",
    license = "GPLv2",
    keywords = "docker yml container",
    packages = find_packages(),
    install_requires = ['pyaml>=17.12.1', 'docker>=3.4.1','six>=1.16.0'],
    scripts = ['autocompose.py'],
    entry_points={
        'console_scripts': [
            'autocompose = autocompose:main',
        ]
    }
)
