# migasfree-imports

This project is used to import external deployments and devices into your Migasfree platform.


## Getting Started

### Cloning the Repository

To use this project, clone it into a working directory:

```bash
git clone https://github.com/migasfree/migasfree-imports.git
cd migasfree-imports
```

### External deployments

This process configures the BASE, UPDATE and SECURITY repositories from the distro base to a Migasfree project, creating a cache of the repositories on your Migasfree server.

The templates are located in  [templates/external-deployments](templates/external-deployments). If your distro base is not listed, please contribute by submitting a pull request to add it.

#### Running the Script

Standard Execution

To run the script, simply execute:

```bash
./external-deployment.py
```

#### Non-Interactive Mode

To run the script without being prompted for input (non-interactive mode), first export the required variables:

```bash
export MIGASFREE_CLIENT_SERVER=migasfree.acme.com
export MIGASFREE_PACKAGER_USER=admin
export MIGASFREE_PACKAGER_PASSWORD=password
export MIGASFREE_PACKAGER_PROJECT=projectname
export DISTRO_BASE=debian_12
./external-deployment.py
```

### Devices

TODO