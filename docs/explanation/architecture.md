# Explanation: Architecture

This document explains the high-level design and data flow of the `migasfree-imports` tool.

## Overview

`migasfree-imports` is a CLI tool designed to synchronize project configurations (deployments, applications) from an external Git repository or a set of JSON templates into a Migasfree server. It acts as a bridge between "Infrastructure as Code" (the JSON templates) and the Migasfree API.

## Data Flow

The following diagram illustrates how data moves from the templates to the Migasfree server.

```mermaid
graph TD
    User([User]) -->|Run Command| Main[migasfree-import]
    
    subgraph "Local Filesystem"
        Templates[JSON Templates]
        Packages[Downloaded Packages]
    end
    
    subgraph "Migasfree Server"
        API[API /api/v1/token/]
        DB[(Database)]
    end
    
    Main -->|Read| Templates
    Main -->|Download (if Source=I)| ExternalRepo[External Repo]
    ExternalRepo -->|Save| Packages
    
    Main -->|Authenticate| API
    Main -->|POST Deployment| API
    Main -->|Upload Packages| API
    
    API -->|Persist| DB
```

## Core Components

### 1. `migasfree-import` (CLI)

The main entry point (formerly `import-project.py`). It orchestrates the entire process:

- Authenticates the user.
- Selects the target Project and Distro Base.
- Iterates through defined Deployments and Applications.
- Calls the API to create/update resources.

### 2. `migasfree_imports.importer.MigasfreeImporter`

The orchestration engine. It separates the business logic from the CLI entry point, handling:

- Selection of distributions and projects.
- Execution of the import workflow (creates platform -> project -> stores -> deployments -> applications).

### 3. `migasfree_imports.client.MigasfreeImport`

A wrapper around the `requests` library, specifically tailored for the Migasfree API. It handles:

- Token-based authentication.
- URL construction.
- Error handling.
- Common API patterns (GET vs POST).

### 4. Templates

The "source of truth" for the import.

- **Deployments**: Define software sources (external repos or internal packages).
- **Applications**: Define catalog items availble to users.

## Design Decisions

- **Idempotency**: The script is designed to be re-runnable. It checks if resources (Projects, Platforms, Stores) exist before attempting to create them (`get_or_post` pattern).
- **Statelessness**: The tool does not maintain a local state database. It relies on the API to determine the current state of the server.
