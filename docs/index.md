# Migasfree Imports Documentation

**Migasfree Imports** is a command-line tool designed to synchronize project configurations (deployments and applications) from external sources into a Migasfree server.

It acts as a bridge between **Infrastructure as Code** (your JSON templates) and the Migasfree API, automating what would otherwise be a manual and repetitive process in the web interface.

## Why use this tool?

If you manage a Migasfree server, `migasfree-imports` allows you to:

1. **Automate Project Setup**: Create entire project hierarchies (Project -> Stores -> Deployments -> Applications) in seconds.
2. **Infrastructure as Code**: Define your software catalog in JSON files (or Git repositories) instead of clicking through the GUI.
3. **Idempotency**: Run the tool as many times as you want; it will only create resources that don't exist, preventing duplicates.
4. **External & Internal Sources**:
    * **External Repositories**: Automatically configure third-party software (e.g., VS Code, Google Chrome).
    * **Internal Packages**: Download `.deb`/`.rpm` files from a URL and upload them to your private Migasfree repository.

## Documentation Structure (Diátaxis)

The documentation is organized into four distinct sections, following the [Diátaxis framework](https://diataxis.fr/):

### 1. [Tutorials](tutorials/getting_started.md) (Learning-oriented)

**"I want to learn by doing."**
Step-by-step lessons that help you get started with `migasfree-imports`. Start here if you are new to the project.

### 2. [How-To Guides](how-to/import_project.md) (Problem-oriented)

**"I want to solve a specific problem."**
Practical guides to help you achieve a specific goal, such as importing a custom project or configuring a new repository source.

### 3. [Reference](reference/api.md) (Information-oriented)

**"I need technical details."**
Technical descriptions of the code, APIs, and command-line interfaces. Use this when you need to know exactly how a function or command works.

### 4. [Explanation](explanation/architecture.md) (Understanding-oriented)

**"I want to understand the background."**
Background information, design decisions, and high-level architecture. Read this to understand *why* things work the way they do.
