from unittest.mock import MagicMock, patch

import pytest

from migasfree_imports.importer import MigasfreeImporter, decode_icon, load_template


@pytest.fixture
def mock_client():
    client = MagicMock()
    # Mock server attribute
    client.server = 'migasfree.test'
    return client


@pytest.fixture
def sample_template():
    return {
        'distros': [{'name': 'Focal', 'platform': 'Ubuntu 20.04', 'pms': 'deb', 'architecture': 'amd64'}],
        'deployments': {
            'Focal': [],
        },
        'applications': [],
    }


@pytest.fixture
def importer(mock_client, sample_template):
    return MigasfreeImporter(mock_client, template=sample_template)


def test_init(importer, mock_client):
    assert importer.client == mock_client
    assert importer.current_date


def test_run_flow(importer, mock_client):
    projects_response = {'results': [{'name': 'TestProject'}]}

    # Mock Client Responses
    mock_client.get.return_value = projects_response
    mock_client.get_or_post.side_effect = [
        [{'id': 1}],  # Platform
        [{'id': 100, 'name': 'TestProject'}],  # Project
    ]

    # Mock Selectors
    with patch('migasfree_imports.importer.select_distro') as mock_select_distro, patch(
        'migasfree_imports.importer.select_project'
    ) as mock_select_project:
        mock_select_distro.return_value = {
            'name': 'Focal',
            'platform': 'Ubuntu 20.04',
            'pms': 'deb',
            'architecture': 'amd64',
        }
        mock_select_project.return_value = 'TestProject'

        with patch.object(importer, '_import_deployments') as mock_deployments, patch.object(
            importer, '_import_applications'
        ) as mock_applications:
            importer.run()

            # Verifications
            mock_select_distro.assert_called()
            mock_select_project.assert_called()
            mock_client.get.assert_called_with('/api/v1/token/projects/')

            # Verify Project Creation
            mock_client.get_or_post.assert_any_call(
                '/api/v1/token/platforms/', params={'name': 'Ubuntu 20.04'}, data={'name': 'Ubuntu 20.04'}
            )

            # Verify Stores Creation (3 calls)
            assert mock_client.post.call_count >= 3

            mock_deployments.assert_called()
            mock_applications.assert_called()


def test_decode_icon():
    """Test decode_icon with a minimal valid 1x1 PNG in base64."""
    import base64

    # Minimal 1x1 transparent PNG
    tiny_png = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
        b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
        b'\r\n\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    b64_data = base64.b64encode(tiny_png).decode()
    data_uri = f'data:image/png;base64,{b64_data}'

    filename, file_obj, mime = decode_icon(data_uri)

    assert filename == 'icon.png'
    assert mime == 'image/png'
    assert file_obj.read() == tiny_png


def test_load_template():
    """Test that the real template.json loads successfully."""
    template = load_template()
    assert 'distros' in template
    assert 'deployments' in template
    assert 'applications' in template
    assert len(template['distros']) > 0
    assert len(template['deployments']) > 0
    assert len(template['applications']) > 0

    # Verify icons are data URIs
    for app in template['applications']:
        assert app['icon'].startswith('data:image/')
