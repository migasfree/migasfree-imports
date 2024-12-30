import os
import requests
import urllib3
urllib3.disable_warnings()

from libs.utils import input_string, input_password, print_inplace


MESSAGES = {
    "/api/v1/token/platforms/": "New Platform: {response[name]} -> https://{self.server}/platforms/results/{response[id]}",
    "/api/v1/token/projects/": "New Project: {response[name]} -> https://{self.server}/projects/results/{response[id]}",
    "/api/v1/token/stores/": "New Store: {response[name]} -> https://{self.server}/stores/results/{response[id]}",
    "/api/v1/token/deployments/": "New Deployment: {response[name]} -> https://{self.server}/deployments/results/{response[id]}",
    "/api/v1/token/catalog/categories/": "New Category: {response[name]} -> https://{self.server}/categories/results/{response[id]}",
    "/api/v1/token/catalog/apps/": "New Application: {response[name]} -> https://{self.server}/applications/results/{response[id]}",
}

class MigasfreeImport:

    def __init__(self, server=None, token=None):
        self.server = server or self.get_server()
        self.token = token or self.get_token()
        self.headers = {"Authorization": f"Token {self.token}"}

    def get_url(self, endpoint):
        return f"https://{self.server}{endpoint}"

    def get_server(self):
        self.server = os.getenv("MIGASFREE_CLIENT_SERVER") or input_string("Server")
        return self.server

    def get_token(self):
        """Retrieve an authentication token from the server."""
        api_url = self.get_url("/token-auth/")
        while True:
            username = os.getenv("MIGASFREE_PACKAGER_USER") or input_string("Username")
            password = os.getenv("MIGASFREE_PACKAGER_PASSWORD") or input_password("Password")
            response = requests.post(api_url, json={'username': username, 'password': password}, verify=False)
            if response.status_code == 200:
                self.token = response.json().get("token")
                self.headers = {"Authorization": f"Token {self.token}"}
                return self.token
            print(f"Error: {response.status_code} - {response.text}. Please try again.")

    def get(self, endpoint, filters={}):
        url=self.get_url(endpoint)
        response = requests.get(url, params=filters, headers=self.headers, verify=False)
        response.raise_for_status()
        return response.json().get("results",{})

    def post(self, endpoint, payload, files={}):
        if files:
            response = requests.post(self.get_url(endpoint), data=payload, files=files, headers=self.headers, verify=False)
        else:
            response = requests.post(self.get_url(endpoint), json=payload, files=files, headers=self.headers, verify=False)
        try:
            _json = response.json()
            print(MESSAGES[endpoint].format(response=_json,self=self))
            return _json
        except:
            pass
        return {}

    def patch(self, endpoint, payload, files={}):
        response = requests.patch(self.get_url(endpoint), data=payload, files=files, headers=self.headers, verify=False)
        response.raise_for_status()
        _json=response.json()
        return _json

    def put(self, endpoint, payload):
        response = requests.put(self.get_url(endpoint), json=payload, headers=self.headers, verify=False)
        response.raise_for_status()
        return response.json()

    def get_or_post(self, endpoint, filters={}, payload={}, files={}):
        element = self.get(endpoint, filters=filters)
        if not element:
            return [self.post(endpoint, payload, files)]
        return element

    def upload_package(self, file_path, project_id, store_id):
        """Upload a package file to the server."""
        print_inplace(f"    Uploading {file_path}")
        url = "/api/v1/token/packages/"
        form_data = {'project': project_id, 'store': store_id}
        with open(file_path, 'rb') as file:
            files = {'files': (os.path.basename(file_path), file, 'application/octet-stream')}
            try:
                response = requests.post(self.get_url(url), data=form_data, files=files, headers=self.headers, verify=False)
                if response.status_code == 201:
                    return response.json()
                print(f"Response status code: {response.status_code}")
                print(f"Response content: {response.text}")
            except requests.exceptions.RequestException as error:
                print(f"Request failed: {error}")
            return {}