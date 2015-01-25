from setuptools import setup, find_packages

setup(
    name = 'webspanner',
    version = '0.1.0',
    keywords = ('asyncio', 'server', 'web'),
    description = 'Spanner is a micro web framework based on asyncio inspired by Flask & Express.js.',
    license = 'MIT License',
    home_page = "https://github.com/ChannelOne/Spanner.py",
    install_requires = ['routes>=2.1'],

    author = 'Simon Chan',
    author_email = 'cdzos97@gmail.com',

    packages = find_packages(),
    platforms = 'any',
)
