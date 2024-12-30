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

    client = MigasfreeImport()

    # DISTRO_BASE
    # ===========
    with open(os.path.join(TEMPLATES_PATH, "distro_base"), "r") as file:
        distro_base = select_distro(json.load(file))

    # SELECT PROJECT
    # ==============
    projects = client.get("/api/v1/token/projects/")
    project_name = select_project(projects)

    print(f"Importing external deployments")
    print(f"==============================")
    print(f"  Server: {client.server}")
    print(f"  Project: {project_name}")
    print(f"  Distro Base: {distro_base['name']}")
    print()

    # PLATFORM
    payload={"name": distro_base["platform"]}
    platform = client.get_or_post("/api/v1/token/platforms/", filters=payload, payload=payload)[0]

    # PROJECT
    # =======
    filters = {"name": project_name}
    payload ={
                "name": project_name,
                "pms": distro_base["pms"],
                "architecture": distro_base["architecture"],
                "auto_register_computers": True,
                "platform": platform["id"]
            }
    project = client.get_or_post("/api/v1/token/projects/", filters=filters, payload=payload)[0]


    # STORES
    # ======
    payload = {"name": "org", "project": project["id"]}
    client.post("/api/v1/token/stores/", payload=payload)
    payload = {"name": "thirds", "project": project["id"]}
    client.post("/api/v1/token/stores/", payload=payload)
    payload = {"name": "updates", "project": project["id"]}
    client.post("/api/v1/token/stores/", payload=payload)


    # DEPLOYMENTS
    # ===========
    with open(os.path.join(TEMPLATES_PATH, "deployments", distro_base["name"]), "r") as file:
        deployments = json.load(file)

    for deployment in deployments:
        if "ignored" in deployment:
            ignored = deployment ["ignored"]
        else:
            ignored = False

        if not ignored:

            if "comment" in deployment:
                variables = {
                    'server': client.server,
                    'project_name': project["name"],
                    'project_slug': slugify(project["name"]),
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
                    "project": project["id"],
                    "included_attributes": deployment["included_attributes"]
                }
                client.post("/api/v1/token/deployments/", payload)

            elif deployment["source"] == "I":
                download_packages(deployment["url_download"], PACKAGES_PATH)

                filters = {"name": deployment["store"], "project__id": project["id"]}
                payload = {"name": deployment["store"], "project": project["id"]}
                store = client.get_or_post("/api/v1/token/stores/", filters=filters, payload=payload)[0]


                # Upload packages
                # ===============
                available_packages = []
                for package in os.listdir(PACKAGES_PATH):
                    if os.path.isfile(os.path.join(PACKAGES_PATH, package)):
                        response = client.upload_package(os.path.join(PACKAGES_PATH, package), project["id"], store["id"])
                        if response:
                            available_packages.append(response["id"])

                shutil.rmtree(PACKAGES_PATH)


                payload = {
                    "enabled": deployment["enabled"],
                    "name": deployment["name"],
                    "comment": "comment",
                    "start_date": current_date,
                    "source": "I",
                    "project": project["id"],
                    "included_attributes": deployment["included_attributes"],
                    "packages_to_install": deployment["packages_to_install"],
                    "packages_to_remove": deployment["packages_to_remove"],
                    "available_packages": available_packages
                }
                client.post("/api/v1/token/deployments/", payload)


    # APPLICATIONS
    # ============
    with open(os.path.join(TEMPLATES_PATH, "applications", "applications"), "r") as file:
        applications = json.load(file)
    for application in applications:
        # Category
        payload = {"name": application["category"]}
        category = client.get_or_post("/api/v1/token/catalog/categories/", filters=payload, payload=payload)[0]
        # Apps
        payload = {
            "name": application["name"],
            "level": application["level"],
            "category": category['id'],
            "score": application["score"],
            "description": application["description"],
            "available_for_attributes": application["available_for_attributes"]
            }
        files = {"icon": (application["icon"], open(f"templates/applications/{application['icon']}","rb"), 'image/png')}
        app = client.get_or_post("/api/v1/token/catalog/apps/", filters={"name": application["name"]}, payload=payload,files=files)[0]
        # Project-Packages
        payload={
            "application": app["id"],
            "packages_to_install": application["packages_to_install"],
            "project": project["id"]
        }
        project_packages = client.get_or_post("/api/v1/token/catalog/project-packages/", filters={"application__id": app["id"],"project__id": project["id"]}, payload=payload)


if __name__ == "__main__":
    main()
