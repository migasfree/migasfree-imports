import base64
import io
import json
import logging
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

from .client import MigasfreeImport
from .utils import download_packages, select_distro, select_project, slugify

GIT_REPO = 'https://github.com/migasfree/migasfree-imports'  # OFFICIAL (default selected)
PACKAGES_PATH = './packages'
TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), '..', 'templates', 'template.json')

logger = logging.getLogger(__name__)


def load_template(path: str = TEMPLATE_FILE) -> Dict[str, Any]:
    """Load the unified template JSON file."""
    with open(path) as file:
        return json.load(file)


def decode_icon(data_uri: str) -> tuple:
    """
    Decode a data URI (data:image/png;base64,...) into binary content
    and return (filename, file_object, mime_type).
    """
    # data:image/png;base64,iVBOR...
    header, encoded = data_uri.split(',', 1)
    mime_type = header.split(':')[1].split(';')[0]  # e.g. image/png
    ext = mime_type.split('/')[1]  # e.g. png
    raw = base64.b64decode(encoded)
    return f'icon.{ext}', io.BytesIO(raw), mime_type


class MigasfreeImporter:
    """
    Handles the orchestration of importing configuration into a migasfree server.
    """

    def __init__(self, client: MigasfreeImport, template: Optional[Dict[str, Any]] = None) -> None:
        self.client = client
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.template = template or load_template()

    def run(self) -> None:
        """
        Executes the import process.
        """
        # DISTRO_BASE
        # ===========
        distro_base = select_distro(self.template['distros'])

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
        deployments = self.template['deployments'][distro_base['name']]

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
        applications: List[Dict[str, Any]] = self.template['applications']

        for application in applications:
            # Category
            payload = {'name': application['category']}
            category = self.client.get_or_post('/api/v1/token/catalog/categories/', params=payload, data=payload)[0]

            # Decode icon from base64 data URI
            icon_filename, icon_file, icon_mime = decode_icon(application['icon'])

            # Apps
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
                        icon_filename,
                        icon_file,
                        icon_mime,
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
