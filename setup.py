from setuptools import setup, find_packages

setup(
    name="spotify-tidal-sync",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "spotipy==2.19.0",
        "tidalapi==0.7.0",
        "PyYAML==6.0",
    ],
    entry_points={
        "console_scripts": [
            "spotify-tidal-sync=main:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to sync playlists between Spotify and Tidal",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/spotify-tidal-sync",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="spotify-tidal-sync",
    version="0.1.0",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "spotify-tidal-sync=main:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to synchronize playlists between Spotify and Tidal",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/spotify-tidal-sync",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
