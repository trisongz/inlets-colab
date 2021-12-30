
# Inlets Colab
 
 Run `CodeServer` on `Colab` using `Inlets` in less than 60 secs using your own domain.
 

---
## Installation

```bash
# From pypi
pip install --upgrade inlets-colab

# From source
pip install --upgrade git+https://github.com/trisongz/inlets-colab

```

---

## Requirements

- [Inlets Server](https://inlets.dev/)

---

## Usage in Colab Notebook

```python

import os
os.environ['INLETS_LICENSE'] = ... # Inlets Pro License
os.environ['INLETS_TOKEN'] = ... # Inlets Token
os.environ['INLETS_TUNNEL_HOST'] = "inlets.domain.com" # Inlets Tunnel Host (ControlPlane)
os.environ['INLETS_SERVER_HOST'] = "colab.domain.com" # Inlets Tunnel Host (DataPlane)
os.environ['INLETS_CLIENT_HOST'] = "127.0.0.1" # The Local Server IP
os.environ['GENERATE_AUTH'] = "true" # Will generate password if not provided
os.environ['MOUNT_GS'] = "true" # Bool to mount GCS Bucket
os.environ['GS_BUCKET'] = "gs_bucket" # Name of GCS Bucket to Mount
os.environ['GS_PROJECT'] = "gcs_project" # Project Name within GCP
os.environ['GS_AUTH'] = ... # Base64 Encoded String of your ServiceAccount.json

from inletscolab.client import InletsColab

InletsColab.start()

```

## Usage in Colab Notebook + Terminal

```python

## Write your env config to envfile.yaml

%%writefile /content/envfile.yaml

INLETS_LICENSE: ...
INLETS_TOKEN: ...
INLETS_TUNNEL_HOST: inlets.domain.com
INLETS_SERVER_HOST: colab.domain.com
INLETS_CLIENT_HOST: 127.0.0.1
GENERATE_AUTH: 'true'
MOUNT_GS: 'true'
GS_BUCKET: gs_bucket
GS_PROJECT: gcs_project
GS_AUTH: ...

```

```bash

## Now use the CLI to launch targeting the envfile.yaml

inletscolab start --envfile /content/envfile.yaml

```


---

## Libraries & Dependencies

- `Python 3.7`

- `lazycls`

- `pylogz`

- `typer`

---

## License

[MIT](./LICENSE)
