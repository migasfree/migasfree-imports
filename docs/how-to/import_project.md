# How-To: Import a Project

This guide explains how to use `migasfree-imports` to import a specific project configuration into your Migasfree server.

## Problem

You want to import a set of deployments and applications defined in a JSON template into a specific Migasfree project.

## Solution

The `migasfree-import` tool automates this process by reading JSON templates and interacting with the Migasfree API.

### 1. Prepare your Environment

Ensure your environment variables are set:

```bash
export MIGASFREE_CLIENT_SERVER="migasfree.example.com"
```

### 2. Select the Distribution Template

The import process relies on templates defined in the `templates/` directory.

- **Deployments**: Defined in `templates/deployments/<distro_name>`.
- **Applications**: Defined in `templates/applications/applications`.

### 3. Run the Import Command

Execute the command:

```bash
migasfree-import
```

### 4. Interactive Selection

If you haven't defined `MIGASFREE_PACKAGER_PROJECT` or `DISTRO_BASE`, the script will ask you to select them interactively.

### 5. Automated Import (Non-Interactive)

To run the import without user intervention (e.g., in a CI/CD pipeline), export all necessary variables:

```bash
export MIGASFREE_CLIENT_SERVER="migasfree.example.com"
export MIGASFREE_PACKAGER_USER="admin"
export MIGASFREE_PACKAGER_PASSWORD="secret_password"
export MIGASFREE_PACKAGER_PROJECT="my-project"
export DISTRO_BASE="ubuntu-22.04"

migasfree-import
```

## Troubleshooting

- **401 Unauthorized**: Check your username and password.
- **Connection Error**: Verify `MIGASFREE_CLIENT_SERVER` is correct and reachable.
- **SSL Error**: Ensure the server has a valid certificate (or `verify=True` is correctly handled if using self-signed certs).
