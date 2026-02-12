import logging
import sys

from .client import MigasfreeImport
from .importer import MigasfreeImporter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main entry point for the script.
    """
    try:
        client = MigasfreeImport()
        importer = MigasfreeImporter(client)
        importer.run()
    except Exception as e:
        logger.error('An error occurred during the import process: %s', e)
        sys.exit(1)


if __name__ == '__main__':
    main()
