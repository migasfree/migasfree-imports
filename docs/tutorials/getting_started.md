# Tutorial: Getting Started with Migasfree Imports

This tutorial will guide you through the initial setup and your first import using `migasfree-imports`. By the end of this tutorial, you will have a working environment and understand the basic command flow.

## Prerequisites

- Python 3.8+ installed
- Access to a Migasfree server
- A valid user token (or credentials) for the Migasfree server

## Step 1: Installation

Clone the repository and install the package (editable mode recommended for dev):

```bash
git clone https://github.com/migasfree/migasfree-imports.git
cd migasfree-imports
pip install -e .
```

## Step 2: Configuration

Set up your environment variables to avoid entering credentials every time:

```bash
export MIGASFREE_CLIENT_SERVER="migasfree.example.com"
export MIGASFREE_PACKAGER_USER="your-username"
export MIGASFREE_PACKAGER_PASSWORD="your-password"
# Optional: Pre-select the distribution base
export DISTRO_BASE="ubuntu-22.04"
```

## Step 3: Running an Import

Run the installed command to start the interactive import process:

```bash
migasfree-import
```

The script will prompt you to:

1. **Select a Project**: Choose the target project on your Migasfree server.
2. **Select a Distro Base**: If not set via env vars, choose the base distribution (e.g., Ubuntu 22.04).

## Step 4: Understanding the Data (Templates)

Migasfree Imports uses JSON templates to define what to import. Here is an example of what these files look like:

**External Repository (e.g., Visual Studio Code):**

```json
{
  "name": "vscode",
  "deployment": {
    "url": "https://packages.microsoft.com/repos/code",
    "distribution": "stable",
    "components": "main",
    "key_url": "https://packages.microsoft.com/keys/microsoft.asc"
  },
  "package": "code"
}
```

**Internal Package:**

```json
{
  "name": "my-internal-package",
  "deployment": {
    "type": "internal",
    "source_url": "http://internal-server/packages/my-package_1.0_all.deb"
  }
}
```

When you run `migasfree-import`, the tool reads these definitions and automatically creates the necessary **Deployments** and **Applications** in your Migasfree server.

## Step 5: Verification

Log in to your Migasfree server web interface and navigate to the project you selected. You should see the imported deployments and applications.

## Next Steps

Now that you have run a basic import, check out the [How-To Guide](../how-to/import_project.md) to learn how to customize the import process.
