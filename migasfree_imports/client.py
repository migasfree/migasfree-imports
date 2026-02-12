import contextlib
import logging
import os
from typing import Any, Dict, List, Optional, Union

import requests
import urllib3

from .utils import print_inplace

urllib3.disable_warnings()

logger = logging.getLogger(__name__)


class MigasfreeImport:
    MESSAGES = {
        '/api/v1/token/platforms/': 'New Platform: {response[name]} -> https://{self.server}/platforms/results/{response[id]}',
        '/api/v1/token/projects/': 'New Project: {response[name]} -> https://{self.server}/projects/results/{response[id]}',
        '/api/v1/token/stores/': 'New Store: {response[name]} -> https://{self.server}/stores/results/{response[id]}',
        '/api/v1/token/deployments/': 'New Deployment: {response[name]} -> https://{self.server}/deployments/results/{response[id]}',
        '/api/v1/token/catalog/categories/': 'New Category: {response[name]} -> https://{self.server}/categories/results/{response[id]}',
        '/api/v1/token/catalog/apps/': 'New Application: {response[name]} -> https://{self.server}/applications/results/{response[id]}',
    }

    def __init__(self, server: Optional[str] = None, token: Optional[str] = None) -> None:
        self.server = server or self.get_server()
        self.token = token or self.get_token()
        self.headers = {'Authorization': f'Token {self.token}'}

    def get_url(self, endpoint: str) -> str:
        return f'http://{self.server}{endpoint}'  # FIXME https

    def get_server(self) -> str:
        server = os.getenv('MIGASFREE_CLIENT_SERVER')
        if not server:
            raise ValueError('MIGASFREE_CLIENT_SERVER environment variable not set.')
        return server

    def get_token(self) -> str:
        """Retrieve an authentication token from the server."""
        api_url = self.get_url('/token-auth/')
        username = os.getenv('MIGASFREE_PACKAGER_USER')
        password = os.getenv('MIGASFREE_PACKAGER_PASSWORD')

        if not username or not password:
            raise ValueError(
                'MIGASFREE_PACKAGER_USER and MIGASFREE_PACKAGER_PASSWORD environment variables must be set.'
            )

        response = requests.post(api_url, json={'username': username, 'password': password}, verify=False)
        if response.status_code == 200:
            self.token = response.json().get('token')
            self.headers = {'Authorization': f'Token {self.token}'}
            return self.token

        logger.error('Error: %s - %s.', response.status_code, response.text)
        raise ConnectionError(f'Could not authenticate with server: {response.text}')

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Helper method to make HTTP requests."""
        url = self.get_url(endpoint)
        response = requests.request(
            method=method, url=url, headers=self.headers, data=data, params=params, files=files, verify=False
        )

        try:
            response.raise_for_status()
            if response.text:
                return response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error('HTTP error occurred: %s', http_err)
        except Exception as err:
            logger.error('Other error occurred: %s', err)

        return {}

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._request('GET', endpoint, params=params)

    def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        response = self._request('POST', endpoint, data=data, files=files)

        if endpoint in self.MESSAGES:
            with contextlib.suppress(Exception):
                logger.info(self.MESSAGES[endpoint].format(response=response, self=self))

        return response

    def patch(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return self._request('PATCH', endpoint, data=data, files=files)

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._request('PUT', endpoint, data=data)

    def get_or_post(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        element = self.get(endpoint, params=params)
        if element:
            return element.get('results', element)

        return [self.post(endpoint, data=data, files=files)]

    def upload_package(self, file_path: str, project_id: int, store_id: int) -> Dict[str, Any]:
        """Upload a package file to the server."""
        print_inplace(f'    Uploading {file_path}')
        url = '/api/v1/token/packages/'
        form_data = {'project': project_id, 'store': store_id}

        with open(file_path, 'rb') as file:
            files = {'files': (os.path.basename(file_path), file, 'application/octet-stream')}
            return self.post(url, data=form_data, files=files)
