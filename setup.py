from setuptools import setup

setup(
    name='obsidianhtml',
    version='0.1',
    description='Converts Obsidian notes into proper markdown and HTML',
    url='https://github.com/obsidian-html/obsidian-html ',
    author='dwrolvink',
    author_email='dwrolvink@protonmail.com',
    license_files = ('LICENSE',),
    packages=['obsidianhtml'],
    install_requires=[
      'markdown',
      'python-frontmatter',
      'pygments'
    ],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'obsidianhtml=obsidianhtml'
        ]
    },
    package_data={'obsidianhtml': ['src/*']},
)