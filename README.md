# migasfree-imports

This project is used to import external deployments and devices into your Migasfree platform.


## Getting Started

### Cloning the Repository

To use this project, clone it into a working directory:

```bash
git clone https://github.com/migasfree/migasfree-imports.git
cd migasfree-imports
```

### Deployments

This process configures the standard repositories (BASE, UPDATE, BACKPORTS, and SECURITY) from the distribution's base system to integrate with a Migasfree project, establishing a repository cache on your Migasfree server.

A local repository is also created with the MigasFree packages to install on the clients.These packages are downloaded from [migasfree.org](migasfree.org).

The templates are located [here](templates). If your distro base is not listed, please contribute by submitting a pull request to add it.

#### Running the Script

Standard Execution

To run the script, simply execute:

```bash
./create-deployments.py
```

#### Non-Interactive Mode

To run the script without being prompted for input (non-interactive mode), first export the required variables:

```bash
export MIGASFREE_CLIENT_SERVER=migasfree.acme.com
export MIGASFREE_PACKAGER_USER=admin
export MIGASFREE_PACKAGER_PASSWORD=password
export MIGASFREE_PACKAGER_PROJECT=projectname
export DISTRO_BASE=debian_12
./create-deployments.py
```

### Devices

TODO