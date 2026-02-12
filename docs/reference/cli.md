# CLI Reference

This section documents the command-line usage of `migasfree-import`.

## Usage

```bash
migasfree-import
```

The script is primarily interactive, but can be automated using environment variables.

## Environment Variables

The following environment variables can be set to configure the import process non-interactively.

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `MIGASFREE_CLIENT_SERVER` | The Migasfree server URL (e.g., `migasfree.example.com`). | Yes | User Prompt |
| `MIGASFREE_PACKAGER_USER` | Attributes to the username used for authentication. | Yes | User Prompt |
| `MIGASFREE_PACKAGER_PASSWORD` | The password for the user. | Yes | User Prompt |
| `MIGASFREE_PACKAGER_PROJECT` | The name of the target project in Migasfree. | No | User Prompt |
| `DISTRO_BASE` | The base distribution to use (must match a folder in `templates/deployments/`). | No | User Prompt |

## Examples

### Interactive Mode

Simply run the script and follow the prompts:

```bash
migasfree-import
```

### Automated Mode

Export the variables and run the script:

```bash
export MIGASFREE_CLIENT_SERVER="migasfree.example.com"
export MIGASFREE_PACKAGER_USER="ci_user"
export MIGASFREE_PACKAGER_PASSWORD="ci_password"
export MIGASFREE_PACKAGER_PROJECT="production"
export DISTRO_BASE="ubuntu-22.04"

migasfree-import
```
