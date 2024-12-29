#!/usr/bin/env python3
import os
import json

import shutil

from datetime import datetime

from libs.migasfreeimport import MigasfreeImport
from libs.utils import select_distro, select_project, download_packages, slugify

GIT_REPO = "https://github.com/migasfree/migasfree-imports" # OFICIAL (default selected)
PACKAGES_PATH = "./packages"
TEMPLATES_PATH = "./templates"

def main():
    """
    Main entry point for the script.
    """

    current_date = datetime.now().strftime("%Y-%m-%d")

    # SERVER
    server = os.getenv("MIGASFREE_CLIENT_SERVER") or input_string("Server")
    client = MigasfreeImport(server)

    # DISTRO_BASE
    with open(os.path.join(TEMPLATES_PATH, "distro_base"), "r") as file:
        distro_base = select_distro(json.load(file))

    # PROJECT
    projects = client.get_projects()
    project_name = select_project(projects)


    with open(os.path.join(TEMPLATES_PATH, "deployments", distro_base["name"]), "r") as file:
        deployments = json.load(file)

    print(f"Importing external deployments")
    print(f"==============================")
    print(f"  Server: {server}")
    print(f"  Project: {project_name}")
    print(f"  Distro Base: {distro_base['name']}")
    print()


    project_id = client.get_or_create_project(project_name, distro_base)


    for deployment in deployments:
        if "ignored" in deployment:
            ignored = deployment ["ignored"]
        else:
            ignored = False

        if not ignored:

            if "comment" in deployment:
                variables = {
                    'server': server,
                    'project_name': project_name,
                    'project_slug': slugify(project_name),
                    'deployment_name': deployment["name"],
                    'deployment_slug': slugify(deployment["name"]),
                }
                comment = deployment['comment'].format(**variables)
            else:
                comment = f"Imported from {GIT_REPO}\nTemplate: {distro_base['name']}"

            if deployment["source"] == "E":
                payload = {
                    "enabled": deployment["enabled"],
                    "name": deployment["name"],
                    "base_url": deployment["base_url"],
                    "comment": comment,
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
                client.create_deployment(payload)

            elif deployment["source"] == "I":

                download_packages(deployment["url_download"], PACKAGES_PATH)

                store_id = client.get_or_create_store(project_id, deployment["store"])

                # Upload packages
                available_packages = []
                for package in os.listdir(PACKAGES_PATH):
                    if os.path.isfile(os.path.join(PACKAGES_PATH, package)):
                        response = client.upload_package(os.path.join(PACKAGES_PATH, package), project_id, store_id )
                        if response:
                            available_packages.append(response["id"])

                shutil.rmtree(PACKAGES_PATH)

                payload = {
                    "enabled": deployment["enabled"],
                    "name": deployment["name"],
                    "comment": comment,
                    "start_date": current_date,
                    "source": "I",
                    "project": project_id,
                    "included_attributes": deployment["included_attributes"],
                    "packages_to_install": deployment["packages_to_install"],
                    "packages_to_remove": deployment["packages_to_remove"],
                    "available_packages": available_packages
                }
                client.create_deployment(payload)

if __name__ == "__main__":
    main()
