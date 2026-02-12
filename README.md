# migasfree-imports

Tool to import external deployments, projects, and applications into a Migasfree server.

## 📚 Documentation

The full documentation is available at [**docs/index.md**](docs/index.md).

It follows the **Diátaxis** framework:

- **[Tutorials](docs/tutorials/getting_started.md)**
- **[How-to Guides](docs/how-to/import_project.md)**
- **[Reference](docs/reference/api.md)**
- **[Explanation](docs/explanation/architecture.md)**

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/migasfree/migasfree-imports.git
cd migasfree-imports
pip install -e .
```

### Usage

Interactive mode:

```bash
migasfree-import
```

Non-interactive mode (using environment variables):

```bash
export MIGASFREE_CLIENT_SERVER=migasfree.example.com
export MIGASFREE_PACKAGER_USER=admin
export MIGASFREE_PACKAGER_PASSWORD=secret
export MIGASFREE_PACKAGER_PROJECT=myproject
migasfree-import
```

See [CLI Reference](docs/reference/cli.md) for all available options.

## 🧪 Testing

Run unit tests with `pytest`:

```bash
PYTHONPATH=. pytest
```
