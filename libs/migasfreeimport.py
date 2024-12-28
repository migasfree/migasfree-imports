import os
import requests
import urllib3
urllib3.disable_warnings()

from libs.utils import input_string, input_password, print_inplace

class MigasfreeImport:
    def __init__(self, server, token=None):
        self.server = server
        self.token = token or self.get_token()
        self.headers = {"Authorization": f"Token {self.token}"}

    def get_url(self, endpoint):
        return f"https://{self.server}{endpoint}"

    def get(self, endpoint):
        response = requests.get(self.get_url(endpoint), headers=self.headers, verify=False)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint, payload):
        response = requests.post(self.get_url(endpoint), json=payload, headers=self.headers, verify=False)
        response.raise_for_status()
        return response.json()

    def put(self, endpoint, payload):
        response = requests.put(self.get_url(endpoint), json=payload, headers=self.headers, verify=False)
        response.raise_for_status()
        return response.json()

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

    def get_platforms(self):
        """Fetch the list of platforms from the server."""
        return self.get("/api/v1/token/platforms/").get("results", [])

    def create_platform(self, payload):
        """Create a new platform on the server."""
        try:
            data = self.post("/api/v1/token/platform/", payload)
            print(f"Platform created: {data['name']} - https://{self.server}/platforms/results/{data['id']}")
            return data
        except requests.exceptions.RequestException as error:
            print(f"Request failed: {error}")

    def get_projects(self):
        """Fetch the list of projects from the server."""
        return self.get("/api/v1/token/projects/").get("results", [])

    def create_project(self, payload):
        """Create a new project on the server."""
        try:
            data = self.post("/api/v1/token/projects/", payload)
            print(f"Project created: {data['name']} - https://{self.server}/stores/results/{data['id']}")
            return data
        except requests.exceptions.RequestException as error:
            print(f"Request failed: {error}")

    def get_stores(self, project_id):
        """Fetch the list of stores associated with a project from the server."""
        try:
            stores = self.get("/api/v1/token/stores/").get("results", [])
            return [store for store in stores if store["project"]["id"] == project_id]
        except requests.exceptions.RequestException as error:
            print(f"Error fetching stores: {error}")
            return []

    def create_store(self, payload):
        """Create a new store on the server."""
        try:
            data = self.post("/api/v1/token/stores/", payload)
            print(f"Store created: {data['name']} - https://{self.server}/stores/results/{data['id']}")
            return data
        except requests.exceptions.RequestException as error:
            print(f"Request failed: {error}")

    def create_deployment(self, payload):
        """Create a new external deployment on the server."""
        try:
            if payload["source"] == "E":
                source = "external"
            else:
                source = "internal"
            data = self.post("/api/v1/token/deployments/", payload)
            print(f"Deployment {source} created: {data['name']} - https://{self.server}/deployments/results/{data['id']}")
        except requests.exceptions.RequestException as error:
            print(f"Request failed: {error}")

    def get_or_create_platform(self, platform_name):
        """Get an existing platform by name or create it if it doesn't exist."""
        platforms = self.get_platforms()
        platform_id = next((platform["id"] for platform in platforms if platform["name"] == platform_name), None)
        if not platform_id:
            result = self.create_platform({"name": platform_name})
            platform_id = result["id"]
        return platform_id

    def get_or_create_project(self, project_name, distro_base):
        """Get an existing project by name or create it if it doesn't exist."""
        projects = self.get_projects()
        project_id = next((project["id"] for project in projects if project["name"] == project_name), None)
        if not project_id:
            platform_id = self.get_or_create_platform(distro_base["platform"])
            payload ={
                "name": project_name,
                "pms": distro_base["pms"],
                "architecture": distro_base["architecture"],
                "auto_register_computers": True,
                "platform": platform_id
            }
            result = self.create_project(payload)
            project_id = result["id"]
            # Create defaults Stores
            self.create_store({"project": project_id,"name": "org"})
            self.create_store({"project": project_id,"name": "updates"})
            self.create_store({"project": project_id,"name": "thirds"})
        return project_id

    def get_or_create_store(self, project_id, store_name):
        """Get an existing store by name or create it if it doesn't exist."""
        stores = self.get_stores(project_id)
        store_id = next((store["id"] for store in stores if store["name"] == store_name), None)
        if not store_id:
            result = self.create_store({"project": project_id, "name": store_name})
            store_id = result["id"]
        return store_id

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
