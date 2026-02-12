import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from migasfree_imports.importer import MigasfreeImporter


@pytest.fixture
def mock_client():
    client = MagicMock()
    # Mock server attribute
    client.server = 'migasfree.test'
    return client


@pytest.fixture
def importer(mock_client):
    return MigasfreeImporter(mock_client)


def test_init(importer, mock_client):
    assert importer.client == mock_client
    assert importer.current_date


def test_run_flow(importer, mock_client):
    # Mock file operations and user selections
    distro_base_content = json.dumps(
        {'name': 'Focal', 'platform': 'Ubuntu 20.04', 'pms': 'deb', 'architecture': 'amd64'}
    )
    projects_response = {'results': [{'name': 'TestProject'}]}

    # Mock Client Responses
    mock_client.get.return_value = projects_response
    mock_client.get_or_post.side_effect = [
        [{'id': 1}],  # Platform
        [{'id': 100, 'name': 'TestProject'}],  # Project
        [{'id': 200}],  # Category
        [{'id': 300}],  # App
        [{'id': 400}],  # Project-Package
        [{'id': 500}],  # Store (for internal deployment)
    ]

    # Mock Selectors
    with patch('builtins.open', mock_open(read_data=distro_base_content)), patch(
        'migasfree_imports.importer.select_distro'
    ) as mock_select_distro, patch('migasfree_imports.importer.select_project') as mock_select_project, patch(
        'migasfree_imports.importer.os.path.join', return_value='dummy_path'
    ):
        mock_select_distro.return_value = {
            'name': 'Focal',
            'platform': 'Ubuntu 20.04',
            'pms': 'deb',
            'architecture': 'amd64',
        }
        mock_select_project.return_value = 'TestProject'

        # Determine which file is being opened to return correct JSON
        # This is complex with mock_open, so we might need a side_effect for open
        # For simplicity, let's assume all json.load calls return compatible structure
        # or we mock the specific methods _import_deployments and _import_applications

        # Let's mock the internal methods to simplify the run test
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
