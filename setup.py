
import os
import sys
from pathlib import Path
from setuptools import setup, find_packages

if sys.version_info.major != 3: raise RuntimeError("This package requires Python 3+")


version = '0.0.0a'
pkg_name = 'inletscolab'
gitrepo = 'trisongz/inlets-colab'
root = Path(__file__).parent

requirements = [
    'lazycls',
    'pylogz',
    'typer',
]

args = {
    'packages': find_packages(include = ['inletscolab', 'inletscolab.*']),
    'install_requires': requirements,
    'long_description': root.joinpath('README.md').read_text(encoding='utf-8'),
    'python_requires': '>=3.7',
    'include_package_data': True,
    'entry_points': {
        'console_scripts': [
            'inletscolab = inletscolab.cmd:cli',
        ]
    }
}

setup(
    name=pkg_name,
    version=version,
    url='https://github.com/trisongz/inlets-colab',
    license='MIT Style',
    description='Port Forward using Inlets with Colab',
    author='trisongz',
    author_email='ts@growthengineai.com',
    long_description_content_type="text/markdown",
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries',
    ],
    **args
)