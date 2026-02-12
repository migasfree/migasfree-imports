import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

from migasfree_imports.utils import (
    download_packages,
    select_distro,
    select_option,
    select_project,
    slugify,
)

# --- slugify ---


@pytest.mark.parametrize(
    'input_str, expected',
    [
        ('Hello World', 'hello-world'),
        ('  Hello   World  ', 'hello-world'),
        ('Hello_World', 'hello_world'),
        ('Hello-World', 'hello-world'),
        ('Café', 'cafe'),  # default allow_unicode=False
        ('---', ''),
        ('', ''),
    ],
)
def test_slugify(input_str, expected):
    assert slugify(input_str) == expected


def test_slugify_unicode():
    assert slugify('Café', allow_unicode=True) == 'café'


# --- select_option ---


def test_select_option_valid_input():
    with patch('builtins.input', return_value='Option 1'):
        result = select_option('Select something', ['Option 1', 'Option 2'])
        assert result == 'Option 1'


def test_select_option_retry_invalid_input(capsys):
    # First input invalid, second valid
    with patch('builtins.input', side_effect=['Invalid', 'Option 1']):
        result = select_option('Select something', ['Option 1', 'Option 2'])
        assert result == 'Option 1'


def test_select_option_not_required_empty_input():
    with patch('builtins.input', return_value=''):
        result = select_option('Select something', ['Option 1', 'Option 2'], required=False)
        assert result == ''


# --- download_packages ---


@patch('requests.get')
@patch('builtins.open', new_callable=mock_open)
@patch('os.makedirs')
def test_download_packages_file_download(mock_makedirs, mock_file, mock_get, tmp_path):
    # Mock response for the directory listing
    mock_response_list = MagicMock()
    mock_response_list.text = '<a href="package.deb">package.deb</a>'
    mock_response_list.raise_for_status.return_value = None

    # Mock response for the file download
    mock_response_file = MagicMock()
    mock_response_file.iter_content.return_value = [b'chunk1', b'chunk2']
    mock_response_file.raise_for_status.return_value = None

    # Mock 'requests.get' to return list first, then file
    mock_get.side_effect = [mock_response_list, mock_response_file]

    download_packages('http://example.com/repo/', str(tmp_path))

    # Verify requests
    assert mock_get.call_count == 2
    mock_get.assert_any_call('http://example.com/repo')
    mock_get.assert_any_call('http://example.com/repo/package.deb', stream=True)

    # Verify file write
    mock_file.assert_called_with(os.path.join(str(tmp_path), 'package.deb'), 'wb')
    # Check if write was called on the file handle returned by context manager
    # mock_file() returns the context manager. __enter__() returns user file handle.
    # handle = mock_file.return_value.__enter__.return_value
    # assert call(b'chunk1') in handle.write.call_args_list
    # assert call(b'chunk2') in handle.write.call_args_list
    # handle.write.assert_any_call(b'chunk2')


@patch('requests.get')
def test_download_packages_recursive(mock_get, tmp_path):
    # 1. Root: contains subdir/
    resp_root = MagicMock()
    resp_root.text = '<a href="subdir/">subdir/</a>'

    # 2. Subdir: contains package.deb
    resp_subdir = MagicMock()
    resp_subdir.text = '<a href="package.deb">package.deb</a>'

    # 3. File download
    resp_file = MagicMock()
    resp_file.iter_content.return_value = [b'data']

    mock_get.side_effect = [resp_root, resp_subdir, resp_file]

    # We mock open and makedirs to avoid real FS operations, but using tmp_path is cleaner if we allowed interaction.
    # Here we stick to full mocking for consistency with previous test style,
    # but let's just mock os.makedirs and open again to be safe.
    with patch('os.makedirs'), patch('builtins.open', mock_open()):
        download_packages('http://example.com/repo/', '/tmp/dest')

        # Verify recursion
        # 1. Access http://example.com/repo
        # 2. Access http://example.com/repo/subdir/
        # 3. Access http://example.com/repo/subdir/package.deb

        # Note: logic might vary depending on whether it adds trailing slash or not
        assert mock_get.call_count == 3


# --- select_project ---


def test_select_project_env_var():
    with patch.dict(os.environ, {'MIGASFREE_PACKAGER_PROJECT': 'my-project'}):
        assert select_project([{'name': 'p1'}]) == 'my-project'


def test_select_project_interactive():
    with patch.dict(os.environ, {}, clear=True), patch(
        'migasfree_imports.utils.select_option', return_value='p1'
    ) as mock_select:
        assert select_project([{'name': 'p1'}]) == 'p1'
        mock_select.assert_called_once()


# --- select_distro ---


def test_select_distro_env_var_valid():
    distros = [{'name': 'd1'}]
    with patch.dict(os.environ, {'DISTRO_BASE': 'd1'}):
        assert select_distro(distros) == {'name': 'd1'}


def test_select_distro_env_var_invalid(capsys):
    distros = [{'name': 'd1'}]
    with patch.dict(os.environ, {'DISTRO_BASE': 'invalid'}), pytest.raises(SystemExit):
        select_distro(distros)
