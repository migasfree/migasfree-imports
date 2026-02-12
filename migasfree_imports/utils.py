import getpass
import logging
import os
import re
import unicodedata
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

EXTENSIONS = ('.deb', '.rpm')

logger = logging.getLogger(__name__)


def print_inplace(*args: Any) -> None:
    """Prints a message in-place on the terminal."""
    print('\033[K', end='')
    print(''.join(map(str, args)), end='\r', flush=True)


def select_distro(distros: List[Dict[str, Any]]) -> Dict[str, Any]:
    distro_name = os.getenv('DISTRO_BASE') or select_option('Distro Base', [distro['name'] for distro in distros])
    selected_distro = next((distro for distro in distros if distro['name'] == distro_name), None)
    if selected_distro:
        return selected_distro

    logger.error("Sorry, distribution '%s' not implemented.", distro_name)
    exit(1)


def select_project(projects: List[Dict[str, Any]]) -> str:
    logger.debug(projects)
    project_name = os.getenv('MIGASFREE_PACKAGER_PROJECT') or select_option(
        'Project', [project['name'] for project in projects], required=False
    )
    return project_name


def get_select(title: str, prompt: str, options: List[str]) -> str:
    print(f'\n{title}')
    for option in options:
        print(f'    - {option}')

    return input(f'{prompt}: ')


def select_option(prompt: str, options: List[str], required: bool = True) -> str:
    """Prompt the user to select an option from a list."""
    title = 'Select a option:' if required else 'Options:'

    while True:
        selection = get_select(title, prompt, options)
        if required:
            if selection in options:
                return selection
        elif selection:
            return selection
        else:
            return selection


def input_string(prompt: str) -> str:
    """Prompt the user to input a string value."""
    while True:
        value = input(f'\n{prompt}: ')
        if value:
            return value


def input_password(prompt: str) -> str:
    """Prompt the user to input a password (masked input)."""
    while True:
        value = getpass.getpass(f'\n{prompt}: ')
        if value:
            return value


def download_packages(
    url: str, destination_directory: str, repository_url: str = '', visited: Optional[Set[str]] = None
) -> None:
    """Recursively download packages from a repository."""
    if not repository_url:
        repository_url = url

    if visited is None:
        visited = set()

    normalized_url = url.rstrip('/')
    if normalized_url in visited:
        return
    visited.add(normalized_url)

    os.makedirs(destination_directory, exist_ok=True)

    try:
        print_inplace(f'    Accessing: {normalized_url}')
        response = requests.get(normalized_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']

            if '?' in href or href.startswith('#') or href.lower() == 'parent directory':
                continue

            resource_url = urljoin(normalized_url + '/', href)

            if not resource_url.startswith(repository_url):
                continue

            if any(href.endswith(ext) for ext in EXTENSIONS):
                file_name = os.path.basename(href)
                file_path = os.path.join(destination_directory, file_name)

                print_inplace(f'    Downloading {resource_url}...')
                with requests.get(resource_url, stream=True) as file_response:
                    file_response.raise_for_status()
                    with open(file_path, 'wb') as file:
                        for chunk in file_response.iter_content(chunk_size=8192):
                            file.write(chunk)
                print_inplace(f'    Saved to {file_path}')

            elif href.endswith('/'):
                download_packages(resource_url, destination_directory, repository_url, visited)

    except requests.RequestException as e:
        logger.error('Error accessing the URL or downloading files: %s', e)


# Copied from django.utils.text.slugify
# Source: https://github.com/django/django/blob/main/django/utils/text.py
# Modifications: None
def slugify(value: Any, allow_unicode: bool = False) -> str:
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')

    value = re.sub(r'[^\w\s-]', '', value.lower())

    return re.sub(r'[-\s]+', '-', value).strip('-_')
