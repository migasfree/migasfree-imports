import json
import logging
import os
import shutil
from datetime import datetime
from typing import Any, Dict

from .client import MigasfreeImport
from .utils import download_packages, select_distro, select_project, slugify

GIT_REPO = 'https://github.com/migasfree/migasfree-imports'  # OFFICIAL (default selected)
PACKAGES_PATH = './packages'
TEMPLATES_PATH = './templates'

logger = logging.getLogger(__name__)


class MigasfreeImporter:
    """
    Handles the orchestration of importing configuration into a migasfree server.
    """

    def __init__(self, client: MigasfreeImport) -> None:
        self.client = client
        self.current_date = datetime.now().strftime('%Y-%m-%d')

    def run(self) -> None:
        """
        Executes the import process.
        """
        # DISTRO_BASE
        # ===========
        with open(os.path.join(TEMPLATES_PATH, 'distro_base')) as file:
            distro_base = select_distro(json.load(file))

        # SELECT PROJECT
        # ==============
        projects = self.client.get('/api/v1/token/projects/')['results']
        project_name = select_project(projects)

        logger.info('Importing external deployments')
        logger.info('==============================')
        logger.info('  Server: %s', self.client.server)
        logger.info('  Project: %s', project_name)
        logger.info('  Distro Base: %s', distro_base['name'])
        print()

        # PLATFORM
        payload = {'name': distro_base['platform']}
        platform = self.client.get_or_post('/api/v1/token/platforms/', params=payload, data=payload)[0]

        # PROJECT
        # =======
        project = self.client.get_or_post(
            '/api/v1/token/projects/',
            params={'name': project_name},
            data={
                'name': project_name,
                'pms': distro_base['pms'],
                'architecture': distro_base['architecture'],
                'auto_register_computers': True,
                'platform': platform['id'],
            },
        )[0]

        # STORES
        # ======
        self.client.post('/api/v1/token/stores/', data={'name': 'org', 'project': project['id']})
        self.client.post('/api/v1/token/stores/', data={'name': 'thirds', 'project': project['id']})
        self.client.post('/api/v1/token/stores/', data={'name': 'updates', 'project': project['id']})

        # DEPLOYMENTS
        # ===========
        self._import_deployments(distro_base, project)

        # APPLICATIONS
        # ============
        self._import_applications(project)

    def _import_deployments(self, distro_base: Dict[str, Any], project: Dict[str, Any]) -> None:
        with open(os.path.join(TEMPLATES_PATH, 'deployments', distro_base['name'])) as file:
            deployments = json.load(file)

        for deployment in deployments:
            ignored = deployment.get('ignored', False)

            if not ignored:
                self._process_deployment(deployment, distro_base, project)

    def _process_deployment(
        self, deployment: Dict[str, Any], distro_base: Dict[str, Any], project: Dict[str, Any]
    ) -> None:
        if 'comment' in deployment:
            variables = {
                'server': self.client.server,
                'project_name': project['name'],
                'project_slug': slugify(project['name']),
                'deployment_name': deployment['name'],
                'deployment_slug': slugify(deployment['name']),
            }
            comment = deployment['comment'].format(**variables)
        else:
            comment = f'Imported from {GIT_REPO}\nTemplate: {distro_base["name"]}'

        if deployment['source'] == 'E':
            self.client.post(
                '/api/v1/token/deployments/',
                data={
                    'enabled': deployment['enabled'],
                    'name': deployment['name'],
                    'base_url': deployment['base_url'],
                    'comment': comment,
                    'start_date': self.current_date,
                    'source': 'E',
                    'options': deployment['options'],
                    'suite': deployment['suite'],
                    'components': deployment['components'],
                    'frozen': deployment['frozen'],
                    'expire': 1440,
                    'project': project['id'],
                    'included_attributes': deployment['included_attributes'],
                },
            )

        elif deployment['source'] == 'I':
            download_packages(deployment['url_download'], PACKAGES_PATH)

            store = self.client.get_or_post(
                '/api/v1/token/stores/',
                params={'name': deployment['store'], 'project__id': project['id']},
                data={'name': deployment['store'], 'project': project['id']},
            )[0]

            # Upload packages
            # ===============
            available_packages = []
            for package in os.listdir(PACKAGES_PATH):
                if os.path.isfile(os.path.join(PACKAGES_PATH, package)):
                    response = self.client.upload_package(
                        os.path.join(PACKAGES_PATH, package), project['id'], store['id']
                    )
                    if response:
                        available_packages.append(response['id'])

            shutil.rmtree(PACKAGES_PATH)

            self.client.post(
                '/api/v1/token/deployments/',
                data={
                    'enabled': deployment['enabled'],
                    'name': deployment['name'],
                    'comment': 'comment',
                    'start_date': self.current_date,
                    'source': 'I',
                    'project': project['id'],
                    'included_attributes': deployment['included_attributes'],
                    'packages_to_install': deployment['packages_to_install'],
                    'packages_to_remove': deployment['packages_to_remove'],
                    'available_packages': available_packages,
                },
            )

    def _import_applications(self, project: Dict[str, Any]) -> None:
        with open(os.path.join(TEMPLATES_PATH, 'applications', 'applications')) as file:
            applications = json.load(file)

        for application in applications:
            # Category
            payload = {'name': application['category']}
            category = self.client.get_or_post('/api/v1/token/catalog/categories/', params=payload, data=payload)[0]

            # Apps
            with open(f'templates/applications/{application["icon"]}', 'rb') as icon_file:
                app = self.client.get_or_post(
                    '/api/v1/token/catalog/apps/',
                    params={'name': application['name']},
                    data={
                        'name': application['name'],
                        'level': application['level'],
                        'category': category['id'],
                        'score': application['score'],
                        'description': application['description'],
                        'available_for_attributes': application['available_for_attributes'],
                    },
                    files={
                        'icon': (
                            application['icon'],
                            icon_file,
                            'image/png',
                        )
                    },
                )[0]

            # Project-Packages
            project_packages = self.client.get_or_post(
                '/api/v1/token/catalog/project-packages/',
                params={'application__id': app['id'], 'project__id': project['id']},
                data={
                    'application': app['id'],
                    'packages_to_install': application['packages_to_install'],
                    'project': project['id'],
                },
            )
            logger.info(project_packages)
