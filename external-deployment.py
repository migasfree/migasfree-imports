#!/usr/bin/env python3
import os
import json
import requests
import urllib3
import getpass
from datetime import datetime

urllib3.disable_warnings()

def select_option(prompt, options):
    """
    Prompt the user to select an option from a list.
    """
    while True:
        print("\nSelect an option:")
        for option in options:
            print(f"    - {option}")
        selection = input(f"{prompt}: ")
        if selection in options:
            return selection

def input_string(prompt):
    """
    Prompt the user to input a string value.
    """
    while True:
        value = input(f"\n{prompt}: ")
        if value:
            return value

def input_password(prompt):
    """
    Prompt the user to input a password (masked input).
    """
    while True:
        value = getpass.getpass(f"\n{prompt}: ")
        if value:
            return value

def get_files(directory):
    """
    Get a list of files in a given directory.
    """
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

def get_token(server):
    """
    Retrieve an authentication token from the server.
    """
    api_url = f"https://{server}/token-auth/"
    while True:
        username = os.getenv("MIGASFREE_PACKAGER_USER") or input_string("Username")
        password = os.getenv("MIGASFREE_PACKAGER_PASSWORD") or input_password("Password")
        payload = {'username': username, 'password': password}

        response = requests.post(api_url, json=payload, verify=False)
        if response.status_code == 200:
            return response.json()["token"]

        print(f"Error: {response.status_code} - {response.text}. Please try again.")

def get_projects(server, token):
    """
    Fetch the list of projects from the server.
    """
    api_url = f"https://{server}/api/v1/token/projects/"
    headers = {"Authorization": f"Token {token}"}

    response = requests.get(api_url, headers=headers, verify=False)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

def list_project_names(projects):
    """
    Extract project names from the list of projects.
    """
    return [project["name"] for project in projects]

def get_project_id(projects, project_name):
    """
    Retrieve the ID of a project by its name.
    """
    for project in projects:
        if project["name"] == project_name:
            return project["id"]
    return None

def create_deployment(server, token, payload):
    """
    Create a new deployment on the server.
    """
    api_url = f"https://{server}/api/v1/token/deployments/"
    headers = {"Authorization": f"Token {token}"}

    try:
        response = requests.post(api_url, json=payload, headers=headers, verify=False)
        if response.status_code == 201:
            data = response.json()
            print(f"Deployment created: {data['name']} - https://{server}/deployments/results/{data['id']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as error:
        print(f"Request failed: {error}")

def main():
    """
    Main entry point for the script.
    """
    git_repo = "https://github.com/migasfree/migasfree-imports"

    server = os.getenv("MIGASFREE_CLIENT_SERVER") or input_string("Server")
    token = get_token(server)

    projects = get_projects(server, token)
    project_name = os.getenv("MIGASFREE_PACKAGER_PROJECT") or select_option("Project", list_project_names(projects))
    project_id = get_project_id(projects, project_name)

    if not project_id:
        print(f"Error: Project '{project_name}' not found.")
        return

    templates_dir = "./templates/external-deployments"
    distro_base = os.getenv("DISTRO_BASE") or select_option("Distro Base", get_files(templates_dir))

    with open(os.path.join(templates_dir, distro_base), "r") as file:
        deployments = json.load(file)

    current_date = datetime.now().strftime("%Y-%m-%d")

    print(f"Importing external deployments")
    print(f"==============================")
    print(f"  Server: {server}")
    print(f"  Project: {project_name}")
    print(f"  Distro Base: {distro_base}")

    for deployment in deployments:
        payload = {
            "enabled": deployment["enabled"],
            "name": deployment["name"],
            "base_url": deployment["base_url"],
            "comment": f"Imported from {git_repo}\nTemplate: {distro_base}",
            "start_date": current_date,
            "source": "E",
            "options": deployment["options"],
            "suite": deployment["suite"],
            "components": deployment["components"],
            "frozen": deployment["frozen"],
            "expire": 1440,
            "project": project_id,
            "included_attributes": deployment["included_attributes"]
        }
        create_deployment(server, token, payload)

if __name__ == "__main__":
    main()
