
# Inlets Colab
 
 Run `CodeServer` on `Colab` using `Inlets` in less than 60 secs using your own domain.

 [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/trisongz/inlets-colab/blob/main/examples/colab_example.ipynb)

### Features

- [x] Optimized for Inlets/InletsPro
- [x] Use your own Custom Domain `i.e. https://colab.yourdomain.com`
- [x] Quick Deployment
- [x] Password Protection (Optional)
- [x] Notebook/CLI Support
- [x] GDrive Integration
- [x] Cloud Storage Integration (gcs, s3, minio, etc.)

**Currently Tested Storage Backends**

- [x] GCP Cloud Storage
- [x] AWS S3
- [ ] Minio

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
os.environ['INLETS_CLIENT_PORT'] = "7070" # The Local Server IP
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
INLETS_CLIENT_PORT: '7070'
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

### **Currently Tested Inlets Server**

- [ ] Inlets in VM
- [x] Inlets in Kubernetes Cluster
    - External:
        - `ExternalDNS`
        - `CertManager`
    - Repo: `https://inlets.github.io/inlets-pro/charts/`
    - Chart: `inlets-pro/inlets-pro`
    - Helm Values:
        - ingress.domain: `$INLETS_TUNNEL_HOST`
        - dataPlane.ports[0].port: `$INLETS_CLIENT_PORT`
        - dataPlane.ports[0].targetPort: `$INLETS_CLIENT_PORT`
    - Provider: `aws-eks`
    - Ingress: 
        - Type: `loadbalancer from nginx-controller`
        - Class: `nginx`
        - Service: `...-inlets-pro-data-plane`
        - Port: `$INLETS_CLIENT_PORT`
        - Path: `/`
        - PathType: `Prefix`
        - Host: `$INLETS_SERVER_HOST`

### **Currently Tested Inlets Cloud Providers**

- [ ] GCP ComputeEngine
- [ ] GCP GKE
- [ ] AWS EC2
- [x] AWS EKS
- [ ] DigitalOcean Droplet
- [ ] DigitalOcean Kubernetes
- [ ] Linode
- [ ] Azure
- [ ] Oracle


---

### Code Server

Default Version: `3.12.0`

Default Plugins:

- [Python](https://open-vsx.org/extension/ms-python/python)

- [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)

- [Jupyter](https://open-vsx.org/extension/ms-toolsai/jupyter)

- [RainbowCSV](https://open-vsx.org/extension/mechatroner/rainbow-csv)

- [VSCode Icons](https://open-vsx.org/extension/vscode-icons-team/vscode-icons)

- [AREPL for Python](https://open-vsx.org/extension/almenon/arepl)

- [Python Indent](https://open-vsx.org/extension/KevinRose/vsc-python-indent)

- [Remote SSH](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh)

- [Tabnine](https://open-vsx.org/extension/TabNine/tabnine-vscode)

- [ResourceMonitor](https://marketplace.visualstudio.com/items?itemName=mutantdino.resourcemonitor)


---

### Environment Variables

Below are the Environment Variables that are used to build the Config

```python

class InletsConfig:
    license: str = Env.to_str('INLETS_LICENSE', '')
    token: str = Env.to_str('INLETS_TOKEN', '')
    tunnel_host: str = Env.to_str('INLETS_TUNNEL_HOST', '')
    server_host: str = Env.to_str('INLETS_SERVER_HOST', '')
    server_port: int = Env.to_int('INLETS_SERVER_PORT', 8123)
    client_host: str = Env.to_str('INLETS_CLIENT_HOST', '127.0.0.1')
    client_port: int = Env.to_int('INLETS_CLIENT_PORT', 7070)
    domain_name: str = Env.to_str('INLETS_DOMAIN', 'localhost')
    is_cluster: bool = Env.to_bool('INLETS_CLUSTER', 'true')
    client_type: str = Env.to_str('INLETS_CLIENT_TYPE', 'tcp')
    use_sudo: bool = Env.to_bool('INLETS_USE_SUDO', 'true')

class ServerConfig:
    extensions: List[str] = Env.to_list('CODESERVER_EXTENSIONS', DefaultCodeServerExtensions)
    version: str = Env.to_str('CODESERVER_VERSION', DefaultCodeServerVersion)
    authtoken: str = Env.to_str('SERVER_AUTHTOKEN', '')
    password: str = Env.to_str('SERVER_PASSWORD', '')
    code: bool = Env.to_bool('RUN_CODE', 'true')
    lab: bool = Env.to_bool('RUN_LAB')
    generate_auth: bool = Env.to_bool('GENERATE_AUTH', 'true')

class StorageConfig:
    
    ## Bool to mount/not mount
    ## should be 'true'/'false'

    mount_drive: bool = Env.to_bool('MOUNT_DRIVE')
    mount_s3: bool = Env.to_bool('MOUNT_S3')
    mount_gs: bool = Env.to_bool('MOUNT_GS')
    mount_minio: bool = Env.to_bool('MOUNT_MINIO')

    ## Paths to Bucket(s)
    ## All bucket should exclude their prefixes
    ## i.e. gs://gsbucket -> gsbucket
    ##      s3://s3bucket -> s3bucket 

    s3_bucket: str = Env.to_str('S3_BUCKET')
    gs_bucket: str = Env.to_str('GS_BUCKET')
    minio_bucket: str = Env.to_str('MINIO_BUCKET')

    ## Paths to Mount Bucket(s)
    ## along with the defaults

    s3_mount_path: str = Env.to_str('S3_MOUNT_PATH', '/content/s3')
    gs_mount_path: str = Env.to_str('GS_MOUNT_PATH', '/content/gs')
    minio_mount_path: str = Env.to_str('MINIO_MOUNT_PATH', '/content/minio')

    ## GCP Cloud Auth
    ## GS_AUTH should be a base64 encoded string of the serviceaccount.json
    ## To create it, run `base64 -i /path/to/serviceaccount.json`
    ## It will likely be _very_ long
    ## If it exists, it will be decoded and saved as proper json to /authz/adc.json

    gauth: PathLike = Env.to_json_b64('GS_AUTH', 'GOOGLE_APPLICATION_CREDENTIALS', '/authz/adc.json')
    gproject: str = Env.to_str('GS_PROJECT')
    
    ## AWS Cloud Auth
    ## Note: as Colab Locations are Randomly selected globally
    ## you may incur increased ingress/egress charges with large files
    ## in your S3 if regions are far apart. Use with Caution

    s3_key_id: str = Env.to_str_env('AWS_KEYID', 'AWS_ACCESS_KEY_ID', '')
    s3_secret: str = Env.to_str_env('AWS_SECRET', 'AWS_SECRET_ACCESS_KEY', '')
    s3_region: str = Env.to_str('AWS_REGION', 'us-east-1')
    
    ## Minio Cloud Auth
    ## Currently Untested
    ## MINIO_ENDPOINT should be the full http/https along with port
    ## i.e. https://minio.yourdomain.com
    ##      http://1.2.3.4:9000

    minio_endpoint: str = Env.to_str('MINIO_ENDPOINT')
    minio_key_id: str = Env.to_str('MINIO_KEYID')
    minio_secret: str = Env.to_str('MINIO_SECRET')


```


---

## Libraries & Dependencies

Python Dependencies

- [lazycls](https://github.com/trisongz/lazycls)

- [pylogz](https://github.com/trisongz/pylogz)

- [typer](https://github.com/tiangolo/typer)

Runtime Dependencies

- [inletsctl](https://github.com/inlets/inlets-pro)

- [codeserver](https://github.com/coder/code-server)

- [gcsfuse](https://github.com/GoogleCloudPlatform/gcsfuse)

- [s3fs-fuse](https://github.com/s3fs-fuse/s3fs-fuse)


---

## Helpful Links

Below are some helpful links in setting up Inlets if you do not already have one set up.

- [Setting Up Inlets Server in Kubernetes Cluster](https://inlets.dev/blog/2021/03/15/scaling-inlets.html)

- [Setting up Inlets Server in VM for Multiple Cloud Providers](https://docs.inlets.dev/tutorial/automated-http-server/)


---

## License

[MIT](LICENSE)
