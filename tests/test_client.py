import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

from migasfree_imports.client import MigasfreeImport


@pytest.fixture
def mock_migasfree_env():
    # Setup environment variables for testing
    with patch.dict(
        os.environ,
        {
            'MIGASFREE_CLIENT_SERVER': 'migasfree.test',
            'MIGASFREE_PACKAGER_USER': 'testuser',
            'MIGASFREE_PACKAGER_PASSWORD': 'testpass',
        },
    ):
        yield


@pytest.fixture
def client(mock_migasfree_env):
    # Mock token retrieval during init if not provided
    with patch.object(MigasfreeImport, 'get_token', return_value='fake-token'):
        return MigasfreeImport()


def test_init_with_defaults(mock_migasfree_env):
    with patch.object(MigasfreeImport, 'get_token', return_value='fake-token'):
        client = MigasfreeImport()
        assert client.server == 'migasfree.test'
        assert client.token == 'fake-token'
        assert client.headers == {'Authorization': 'Token fake-token'}
        # Because we patch get_token, it is called by __init__
        # But wait, original code says `self.token = token or self.get_token()`
        # If we patch `get_token` on the class, calls to `self.get_token()` will use the mock


def test_init_with_args():
    client = MigasfreeImport(server='custom.server', token='custom-token')
    assert client.server == 'custom.server'
    assert client.token == 'custom-token'
    assert client.headers == {'Authorization': 'Token custom-token'}


def test_get_url(client):
    # Update to https if fixed, currently http per code
    assert client.get_url('/api/test') == 'http://migasfree.test/api/test'


def test_get_token_success(mock_migasfree_env):
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'token': 'new-token'}
        mock_post.return_value = mock_response

        # Instantiate without calling get_token automatically
        with patch.object(MigasfreeImport, 'get_token'):
            client = MigasfreeImport(token='initial')

        token = client.get_token()

        assert token == 'new-token'
        assert client.headers['Authorization'] == 'Token new-token'
        mock_post.assert_called_with(
            'http://migasfree.test/token-auth/', json={'username': 'testuser', 'password': 'testpass'}, verify=False
        )


def test_get_token_failure_missing_env(mock_migasfree_env):
    with patch.dict(os.environ, {}, clear=True), patch.dict(os.environ, {'MIGASFREE_CLIENT_SERVER': 'migasfree.test'}):
        # 1. Instantiate with a mock to bypass __init__ check
        with patch.object(MigasfreeImport, 'get_token', return_value='fake'):
            client = MigasfreeImport()

        # 2. Call real get_token() which should fail because env vars are missing
        with pytest.raises(ValueError, match='must be set'):
            client.get_token()


def test_get_token_auth_failure(mock_migasfree_env):
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_post.return_value = mock_response

        with patch.object(MigasfreeImport, 'get_token', return_value='fake'):
            client = MigasfreeImport()

        with pytest.raises(ConnectionError, match='Could not authenticate'):
            client.get_token()


def test_request_methods(client):
    with patch('requests.request') as mock_req:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"key": "value"}'
        mock_resp.json.return_value = {'key': 'value'}
        mock_req.return_value = mock_resp

        # GET
        assert client.get('/endpoint') == {'key': 'value'}
        mock_req.assert_called_with(
            method='GET',
            url='http://migasfree.test/endpoint',
            headers=client.headers,
            data=None,
            params=None,
            files=None,
            verify=False,
        )

        # POST
        client.post('/endpoint', data={'d': 1})
        mock_req.assert_called_with(
            method='POST',
            url='http://migasfree.test/endpoint',
            headers=client.headers,
            data={'d': 1},
            params=None,
            files=None,
            verify=False,
        )

        # PUT
        client.put('/endpoint', data={'d': 2})
        mock_req.assert_called_with(
            method='PUT',
            url='http://migasfree.test/endpoint',
            headers=client.headers,
            data={'d': 2},
            params=None,
            files=None,
            verify=False,
        )

        # PATCH
        client.patch('/endpoint', data={'d': 3})
        mock_req.assert_called_with(
            method='PATCH',
            url='http://migasfree.test/endpoint',
            headers=client.headers,
            data={'d': 3},
            params=None,
            files=None,
            verify=False,
        )


def test_get_or_post_existing(client):
    with patch.object(client, 'get', return_value={'results': [{'id': 1}]}) as mock_get:
        assert client.get_or_post('/endpoint') == [{'id': 1}]
        mock_get.assert_called_once()


def test_get_or_post_new(client):
    with patch.object(client, 'get', return_value=None) as mock_get, patch.object(
        client, 'post', return_value={'id': 2}
    ) as mock_post:
        assert client.get_or_post('/endpoint', data={'a': 1}) == [{'id': 2}]
        mock_get.assert_called_once()
        mock_post.assert_called_once_with('/endpoint', data={'a': 1}, files=None)


def test_upload_package(client):
    with patch('builtins.open', mock_open(read_data=b'data')), patch.object(
        client, 'post', return_value={'id': 99}
    ) as mock_post:
        res = client.upload_package('pkg.deb', 1, 2)
        assert res == {'id': 99}

        # Check if post was called (params verification is a bit complex due to file object)
        mock_post.assert_called()
        _, kwargs = mock_post.call_args
        assert kwargs['data'] == {'project': 1, 'store': 2}
        assert 'files' in kwargs
