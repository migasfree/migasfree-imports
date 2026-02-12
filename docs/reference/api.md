# API Reference

This section documents the core classes and functions used in `migasfree-imports`.

## `migasfree_imports.client.MigasfreeImport`

The main client class for interacting with the Migasfree API.

```python
class MigasfreeImport:
    def __init__(self, server=None, token=None):
        """
        Initialize the Migasfree client.
        
        Args:
            server (str, optional): The Migasfree server URL (e.g., "migasfree.example.com").
                                    Defaults to MIGASFREE_CLIENT_SERVER env var.
            token (str, optional): Authentication token. Defaults to retrieving a new token.
        """
```

### Methods

#### `get_token(self)`

Retrieves an authentication token from the server using username/password.

- **Returns**: `str` (Token)
- **Raises**: `requests.HTTPError` if authentication fails.

#### `get(self, endpoint, params=None)`

Performs a GET request to the specified endpoint.

- **Args**:
  - `endpoint` (str): API endpoint (e.g., `/api/v1/token/projects/`).
  - `params` (dict, optional): Query parameters.
- **Returns**: `dict` (JSON response) or `None`.

#### `post(self, endpoint, data=None, files=None)`

Performs a POST request to create a new resource.

- **Args**:
  - `endpoint` (str): API endpoint.
  - `data` (dict, optional): JSON payload.
  - `files` (dict, optional): Files to upload.
- **Returns**: `dict` (JSON response).

## `migasfree_imports.importer.MigasfreeImporter`

Handles the orchestration of the import process.

```python
class MigasfreeImporter:
    def __init__(self, client):
        """
        Initialize the importer with a configured client.
        
        Args:
            client (MigasfreeImport): An instance of the API client.
        """

    def run(self):
        """
        Executes the full import workflow:
        1. Selects Distro Base.
        2. Selects Project.
        3. Creates/Updates Platform, Project, and Stores.
        4. Imports Deployments and Applications.
        """
```

## `migasfree_imports.utils`

Utility functions for the import process.

### `download_packages(url, destination_directory, repository_url="", visited=None)`

Recursively downloads packages from a repository URL.

- **Args**:
  - `url` (str): The current URL to crawl.
  - `destination_directory` (str): Local path to save files.
  - `repository_url` (str): The base URL of the repository (to prevent escaping).
  - `visited` (set): To track visited URLs and prevent loops.
