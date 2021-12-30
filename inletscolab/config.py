from lazycls.envs import Env
from lazycls.prop import classproperty
from lazycls.types import *
from lazycls.io import Path, PathLike
from lazycls.serializers import Base
from lazycls.utils import find_binary_in_path, exec_shell
from logz import get_logger
from uuid import uuid1


try:
    from google.colab import drive # type: ignore
    colab_env = True
except ImportError:
    colab_env = False


authz_dir = Path('/authz')
authz_dir.mkdir(parents=True, exist_ok=True)
root_dir = Path.get_parent_path(__file__)

bin_dir = root_dir.joinpath('bin')
scripts_dir = root_dir.joinpath('scripts')
user_exec_dir = Path('/usr/local/bin')

_inlets_installer = scripts_dir.joinpath('get_inlets.sh')
_inlets_exec = user_exec_dir.joinpath('inletsctl')

_cs_installer = scripts_dir.joinpath('get_codeserver.sh')

CSDefaultExtensions = ["ms-python.python", "ms-toolsai.jupyter", "mechatroner.rainbow-csv", "vscode-icons-team.vscode-icons", "tabnine.tabnine-vscode", "almenon.arepl", "kevinrose.vsc-python-indent", "ms-vscode-remote.remote-ssh", "mutantdino.resourcemonitor", "ms-python.vscode-pylance"]
CSDefaultVersion = "3.12.0"

logger = get_logger('InletsColab')

DebugEnabled: bool = Env.to_bool('DEBUG_ENABLED')

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

    @classmethod
    def update_config(cls, **kwargs):
        for k,v in kwargs.items():
            if getattr(cls, k, None): setattr(cls, k, v)

    @classproperty
    def inlets_dir(cls):
        return authz_dir.joinpath('.inlets')

    @classproperty
    def lincense_file(cls):
        cls.inlets_dir.mkdir(parents=True, exist_ok=True)
        return cls.inlets_dir.joinpath('license')

    @classproperty
    def inlets_exists(cls):
        return _inlets_exec.exists()
    
    @classproperty
    def tunnel_url(cls):
        if cls.is_cluster: return f'wss://{cls.tunnel_host}'
        return f'wss://{cls.server_host}:{cls.server_port}/connect'
    
    @classproperty
    def public_url(cls):
        if cls.is_cluster: return f'https://{cls.server_host}'
        if cls.domain_name: return f'https://{cls.domain_name}'
        return f'http://{cls.client_host}:{cls.client_port}'
        

    @classproperty
    def upstream(cls): return cls.client_host

    @classproperty
    def upstream_port(cls): return cls.client_port

    @classproperty
    def systemd_path(cls):
        return Path('/etc/systemd/system/inlets.service')

    @classproperty
    def upstream_url(cls):
        if cls.domain_name: return f'{cls.domain_name}=http://{cls.client_host}:{cls.client_port}'
        return f'http://{cls.client_host}:{cls.client_port}'

    @classmethod
    def get_cmd(cls):
        cmd = f'inlets-pro {cls.client_type} client --url={cls.tunnel_url}' 
        if cls.is_cluster: cmd += f' --upstream={cls.upstream} --port={cls.upstream_port} --auto-tls=false'
        else:  cmd += f' --upstream={cls.upstream_url}'
        if cls.token: cmd += f' --token={cls.token}'
        if cls.license: cmd += f' --license-file={cls.lincense_file.string}'
        if cls.use_sudo: cmd = 'sudo ' + cmd 
        return cmd
    

    @classmethod
    def create_service(cls):
        """ Creates a systemd service """
        if cls.systemd_path.exists(): return
        cmd = cls.get_cmd()
        cmd += f" --generate systemd > {cls.systemd_path.string}"
        exec_shell(cmd)


    @classmethod
    def get_env(cls):
        return {
            'LICENSE': cls.lincense_file.string
        }

    @classmethod
    def create_license(cls, license: str = None, overwrite: bool = False):
        if not cls.license or license: return
        if cls.lincense_file.exists() and not overwrite: return
        license = license or cls.license
        cls.lincense_file.write_text(license)
        cls.license = license

    @classmethod
    def ensure_inlets(cls, overwrite: bool = False):
        if cls.inlets_exists and not overwrite: return
        logger.info(f'Setting up Inlets. This will take a moment.')
        exec_shell(f'sudo bash {_inlets_installer.string}')
        exec_shell('sudo inletsctl download')
    
    @classmethod
    def display_info(cls):
        msg = "\n\nInlets Client is Running at: "
        if cls.is_cluster: msg += f" {cls.server_host}"
        else: msg+= f" {cls.domain_name}"
        msg += f". Listening to: http://{cls.client_host}:{cls.client_port}\n\n"
        logger.info(msg)
        logger.warn('Setup is not complete until Server is running.')

    @classmethod
    def export_config(cls):
        return {
            'INLETS_LICENSE': cls.license,
            'INLETS_TOKEN': cls.token,
            'INLETS_TUNNEL_HOST': cls.tunnel_host,
            'INLETS_SERVER_HOST': cls.server_host,
            'INLETS_SERVER_PORT': cls.server_port,
            'INLETS_CLIENT_HOST': cls.client_host,
            'INLETS_CLIENT_PORT': cls.client_port,
            'INLETS_DOMAIN': cls.domain_name,
            'INLETS_CLIENT_TYPE': cls.client_type,
            'INLETS_CLUSTER': cls.is_cluster,
            'INLETS_USE_SUDO': cls.use_sudo        
        }
    
    @classmethod
    def reload_from_env(cls):
        logger.info(f'Reloading InletsConfig from Environment')
        cls.license: str = Env.to_str('INLETS_LICENSE', cls.license)
        cls.token: str = Env.to_str('INLETS_TOKEN', cls.token)
        cls.tunnel_host: str = Env.to_str('INLETS_TUNNEL_HOST', cls.tunnel_host)
        cls.server_host: str = Env.to_str('INLETS_SERVER_HOST', cls.server_host)
        cls.server_port: int = Env.to_int('INLETS_SERVER_PORT', cls.server_port)
        cls.client_host: str = Env.to_str('INLETS_CLIENT_HOST', cls.client_host)
        cls.client_port: int = Env.to_int('INLETS_CLIENT_PORT', cls.client_port)
        cls.domain_name: str = Env.to_str('INLETS_DOMAIN', cls.domain_name)
        cls.is_cluster: bool = Env.to_bool('INLETS_CLUSTER') or cls.is_cluster
        cls.client_type: str = Env.to_str('INLETS_CLIENT_TYPE', cls.client_type)
        cls.use_sudo: bool = Env.to_bool('INLETS_USE_SUDO') or cls.use_sudo
        

    

class ServerConfig:
    extensions: List[str] = Env.to_list('CODESERVER_EXTENSIONS', CSDefaultExtensions)
    version: str = Env.to_str('CODESERVER_VERSION', CSDefaultVersion)
    authtoken: str = Env.to_str('SERVER_AUTHTOKEN', '')
    password: str = Env.to_str('SERVER_PASSWORD', '')
    code: bool = Env.to_bool('RUN_CODE', 'true')
    lab: bool = Env.to_bool('RUN_LAB')
    generate_auth: bool = Env.to_bool('GENERATE_AUTH', 'true')
    lab_token: str = None
    

    @classmethod
    def update_config(cls, **kwargs):
        for k,v in kwargs.items():
            if getattr(cls, k, None): setattr(cls, k, v)

    @classproperty
    def cs_exists(cls):
        return find_binary_in_path('code-server')
    
    @classproperty
    def cs_exec_script(cls): return scripts_dir.joinpath('run_codeserver.sh')

    @classproperty
    def is_colab(cls):
        return colab_env
    
    @classmethod
    def ensure_codeserver(cls):
        if cls.cs_exists or not cls.is_colab: return
        logger.info(f'Setting up CodeServer ver. {cls.version}')
        exec_shell(f'sudo bash {_cs_installer.string} --version {cls.version}')
        for ext in cls.extensions:
            exec_shell(f'code-server --install-extension {ext}')

    @classmethod
    def get_authtoken(cls):
        if cls.authtoken or not cls.generate_auth: return cls.authtoken
        return Base.get_uuid()

    @classmethod
    def get_lab_token(cls):
        return str(uuid1())

    @classmethod
    def get_code_password(cls):
        if cls.password or not cls.generate_auth: return cls.password
        return Base.get_uuid()
    
    @classmethod
    def get_lab_password(cls):
        if cls.password or not cls.generate_auth: return cls.password
        return Base.get_uuid()

    @classproperty
    def port(cls):
        return InletsConfig.client_port
    
    @classproperty
    def host(cls):
        return InletsConfig.client_host
    
    @classproperty
    def public_url(cls):
        return InletsConfig.public_url


    @classmethod
    def get_lab_cmd(cls):
        cmd = f"jupyter-lab --ip='{cls.host}' --allow-root --ServerApp.allow_remote_access=True --no-browser"
        cls.token = cls.get_lab_token()
        password = cls.get_lab_password()
        if password: 
            cls.password = password
            cmd += f" --ServerApp.token='{cls.token}' --ServerApp.password='{password}' --port={cls.port}"
        else: cmd += f" --ServerApp.token='{cls.token}' --ServerApp.password='' --port={cls.port}"
        return cmd

    @classmethod
    def get_codeserver_cmd(cls):
        password = cls.get_code_password()
        if password: cls.password = password
        return f'bash {cls.cs_exec_script.string} "{cls.host}:{cls.port}" "{cls.password}"'
        
    @classmethod
    def get_cmd(cls):
        if cls.code: return cls.get_codeserver_cmd()
        return cls.get_lab_cmd()

    @classmethod
    def display_info(cls):
        msg = "Running: "
        if cls.code: 
            msg += f"CodeServer v{cls.version}"
        elif cls.lab: 
            msg += "Jupyter Lab"
            if cls.lab_token: msg += f" Token: {cls.lab_token}"
        msg += f" @ {cls.host}:{cls.port}"
        logger.info(msg)
        if cls.code: logger.info(f'\n\nYour CodeServer is Available Here: {cls.public_url}/?folder=/content\n')
        if cls.password: logger.info(f'\n\nYour CodeServer Password: {cls.password}\n')
    
    
    @classmethod
    def reload_from_env(cls):
        logger.info(f'Reloading ServerConfig from Environment')
        cls.extensions: List[str] = Env.to_list('CODESERVER_EXTENSIONS', cls.extensions)
        cls.version: str = Env.to_str('CODESERVER_VERSION', cls.version)
        cls.authtoken: str = Env.to_str('SERVER_AUTHTOKEN', cls.authtoken)
        cls.password: str = Env.to_str('SERVER_PASSWORD', cls.password)
        cls.code: bool = Env.to_bool('RUN_CODE') or cls.code
        cls.lab: bool = Env.to_bool('RUN_LAB') or cls.lab
        cls.generate_auth: bool = Env.to_bool('GENERATE_AUTH') or cls.generate_auth

    @classmethod
    def export_config(cls):
        return {
            'CODESERVER_EXTENSIONS': cls.extensions,
            'CODESERVER_VERSION': cls.version,
            'SERVER_AUTHTOKEN': cls.authtoken,
            'SERVER_PASSWORD': cls.password,
            'RUN_CODE': cls.code,
            'RUN_LAB': cls.lab,
            'GENERATE_AUTH': cls.generate_auth
        }



class StorageConfig:
    mount_drive: bool = Env.to_bool('MOUNT_DRIVE')
    mount_s3: bool = Env.to_bool('MOUNT_S3')
    mount_gs: bool = Env.to_bool('MOUNT_GS')
    mount_minio: bool = Env.to_bool('MOUNT_MINIO')
    s3_bucket: str = Env.to_str('S3_BUCKET')
    gs_bucket: str = Env.to_str('GS_BUCKET')
    minio_bucket: str = Env.to_str('MINIO_BUCKET')
    s3_mount_path: str = Env.to_str('S3_MOUNT_PATH', '/content/s3')
    gs_mount_path: str = Env.to_str('GS_MOUNT_PATH', '/content/gs')
    minio_mount_path: str = Env.to_str('MINIO_MOUNT_PATH', '/content/minio')
    ## Auths
    ### GCP
    gauth: PathLike = Env.to_json_b64('GS_AUTH', 'GOOGLE_APPLICATION_CREDENTIALS', '/authz/adc.json')
    gproject: str = Env.to_str('GS_PROJECT')
    ### AWS
    s3_key_id: str = Env.to_str_env('AWS_KEYID', 'AWS_ACCESS_KEY_ID', '')
    s3_secret: str = Env.to_str_env('AWS_SECRET', 'AWS_SECRET_ACCESS_KEY', '')
    s3_region: str = Env.to_str('AWS_REGION', 'us-east-1')
    ### Minio
    minio_endpoint: str = Env.to_str('MINIO_ENDPOINT')
    minio_key_id: str = Env.to_str('MINIO_KEYID')
    minio_secret: str = Env.to_str('MINIO_SECRET')
    ### Backups / Not Used ATM
    storage_backup: str = Env.to_str('STORAGE_BACKUP', '')
    
    @classmethod
    def update_config(cls, **kwargs):
        for k,v in kwargs.items():
            if getattr(cls, k, None): setattr(cls, k, v)

    @classmethod
    def mount_gdrive(cls, force: bool = False):
        if cls.mount_drive or force and colab_env: drive.mount("/content/drive")
    
    @classmethod
    def setup_storage(cls, **kwargs):
        if kwargs: cls.update_config(**kwargs)
        cls.write_envfile()
        cls.write_botofile()
        cls.mount_gdrive()
        if cls.has_mounts:
            logger.info(f'Setting up Storage. This may take a while...')
            exec_shell(f'sudo bash {cls.storage_setup_exec_script.string}')
    
    @classproperty
    def has_mounts(cls):
        return any([cls.mount_gs, cls.mount_s3, cls.mount_minio])
    
    @classproperty
    def envfile(cls): return scripts_dir.joinpath('load_env.sh')

    @classproperty
    def botofile(cls): return authz_dir.joinpath('.boto')
    
    @classproperty
    def storage_setup_exec_script(cls): return scripts_dir.joinpath('setup_storage.sh')
    
    @classproperty
    def storage_run_exec_script(cls): return scripts_dir.joinpath('run_storage.sh')
    
    @classproperty
    def s3_endpoint(cls): return f'https://s3.{cls.s3_region}.amazonaws.com'
    
    @classmethod
    def write_envfile(cls):
        if DebugEnabled: logger.info(f'Writing Envfile to {cls.envfile.string}')
        cls.envfile.write_text(cls.get_envfile_values())
    
    @classmethod
    def write_botofile(cls):
        if DebugEnabled: logger.info(f'Writing Botofile to {cls.botofile.string}')
        cls.botofile.write_text(cls.get_boto_values())
    
    @classmethod
    def get_envfile_data(cls):
        return {
            'MOUNT_DRIVE': cls.mount_drive,
            'MOUNT_S3': cls.mount_s3,
            'MOUNT_MINIO': cls.mount_minio,
            'S3_BUCKET': cls.s3_bucket,
            'S3_MOUNT_PATH': cls.s3_mount_path,
            'AWS_ACCESS_KEY_ID': cls.s3_key_id,
            'AWS_SECRET_ACCESS_KEY': cls.s3_secret,
            'AWS_REGION': cls.s3_region,
            'S3_ENDPOINT': cls.s3_endpoint,
            'GOOGLE_APPLICATION_CREDENTIALS': cls.gauth.as_posix(),
            'GS_BUCKET': cls.gs_bucket,
            'GS_MOUNT_PATH': cls.gs_mount_path,
            'MINIO_BUCKET': cls.minio_bucket,
            'MINIO_MOUNT_PATH': cls.minio_mount_path,
            'MINIO_ENDPOINT': cls.minio_endpoint,
            'MINIO_ACCESS_KEY': cls.minio_key_id,
            'MINIO_SECRET_KEY': cls.minio_secret,
            'BOTO_PATH': cls.botofile.string,
            'BOTO_CONFIG': cls.botofile.string,
            'STORAGE_BACKUP': cls.storage_backup,
        }

    @classmethod
    def get_boto_values(cls):
        t = "[Credentials]\n"
        if cls.s3_key_id:
            t += f"aws_access_key_id = {cls.s3_key_id}\n"
            t += f"aws_secret_access_key = {cls.s3_secret}\n"
        if cls.gauth.exists():
            t += f"gs_service_key_file = {cls.gauth.as_posix()}\n"
        t += "\n[Boto]\n"
        t += "https_validate_certificates = True\n"
        t += "\n[GSUtil]\n"
        t += "content_language = en\n"
        t += "default_api_version = 2\n"
        if cls.gproject:
            t+= f"default_project_id = {cls.gproject}\n"
        return t
    
    @classmethod
    def get_envfile_values(cls):
        t = f"""
#!/bin/bash

## This is the file used to load the envs

export MOUNT_DRIVE={cls.mount_drive}
export MOUNT_S3={cls.mount_s3}
export MOUNT_GS={cls.mount_gs}
export MOUNT_MINIO={cls.mount_minio}

export S3_BUCKET={cls.s3_bucket}
export S3_MOUNT_PATH={cls.s3_mount_path}
export AWS_ACCESS_KEY_ID={cls.s3_key_id}
export AWS_SECRET_ACCESS_KEY={cls.s3_secret}
export AWS_REGION={cls.s3_region}
export S3_ENDPOINT={cls.s3_endpoint}

export GOOGLE_APPLICATION_CREDENTIALS={cls.gauth.as_posix()}
export GS_BUCKET={cls.gs_bucket}
export GS_MOUNT_PATH={cls.gs_mount_path}

export MINIO_BUCKET={cls.minio_bucket}
export MINIO_MOUNT_PATH={cls.minio_mount_path}
export MINIO_ENDPOINT={cls.minio_endpoint}
export MINIO_ACCESS_KEY={cls.minio_key_id}
export MINIO_SECRET_KEY={cls.minio_secret}

export BOTO_PATH={cls.botofile.string}
export BOTO_CONFIG={cls.botofile.string}

export STORAGE_BACKUP={cls.storage_backup}
"""
        return t
    
    @classmethod
    def export_config(cls):
        return {
            'MOUNT_DRIVE': cls.mount_drive,
            'MOUNT_S3': cls.mount_s3,
            'MOUNT_MINIO': cls.mount_minio,
            'S3_BUCKET': cls.s3_bucket,
            'S3_MOUNT_PATH': cls.s3_mount_path,
            'AWS_KEYID': cls.s3_key_id,
            'AWS_SECRET': cls.s3_secret,
            'AWS_REGION': cls.s3_region,
            'S3_ENDPOINT': cls.s3_endpoint,
            'GS_AUTH': cls.gauth.read_text(),
            'GS_BUCKET': cls.gs_bucket,
            'GS_MOUNT_PATH': cls.gs_mount_path,
            'MINIO_BUCKET': cls.minio_bucket,
            'MINIO_MOUNT_PATH': cls.minio_mount_path,
            'MINIO_ENDPOINT': cls.minio_endpoint,
            'MINIO_ACCESS_KEY': cls.minio_key_id,
            'MINIO_SECRET_KEY': cls.minio_secret,
            'STORAGE_BACKUP': cls.storage_backup
        }
    
    @classmethod
    def reload_from_env(cls):
        logger.info(f'Reloading StorageConfig from Environment')
        cls.mount_drive: bool = Env.to_bool('MOUNT_DRIVE') or cls.mount_drive
        cls.mount_s3: bool = Env.to_bool('MOUNT_S3') or cls.mount_s3
        cls.mount_gs: bool = Env.to_bool('MOUNT_GS') or cls.mount_gs
        cls.mount_minio: bool = Env.to_bool('MOUNT_MINIO') or cls.mount_minio
        cls.s3_bucket: str = Env.to_str('S3_BUCKET', cls.s3_bucket)
        cls.gs_bucket: str = Env.to_str('GS_BUCKET', cls.gs_bucket)
        cls.minio_bucket: str = Env.to_str('MINIO_BUCKET', cls.minio_bucket)
        cls.s3_mount_path: str = Env.to_str('S3_MOUNT_PATH', cls.s3_mount_path)
        cls.gs_mount_path: str = Env.to_str('GS_MOUNT_PATH', cls.gs_mount_path)
        cls.minio_mount_path: str = Env.to_str('MINIO_MOUNT_PATH', cls.minio_mount_path)
        ### GCP
        cls.gauth: Type(Path) = Env.to_json_b64('GS_AUTH', 'GOOGLE_APPLICATION_CREDENTIALS', cls.gauth.as_posix())
        ### AWS
        cls.s3_key_id: str = Env.to_str_env('AWS_KEYID', 'AWS_ACCESS_KEY_ID', cls.s3_key_id)
        cls.s3_secret: str = Env.to_str_env('AWS_SECRET', 'AWS_SECRET_ACCESS_KEY', cls.s3_secret)
        cls.s3_region: str = Env.to_str('AWS_REGION', cls.s3_region)
        ### Minio
        cls.minio_endpoint: str = Env.to_str('MINIO_ENDPOINT', cls.minio_endpoint)
        cls.minio_key_id: str = Env.to_str('MINIO_KEYID', cls.minio_key_id)
        cls.minio_secret: str = Env.to_str('MINIO_SECRET', cls.minio_secret)
        ### Backup
        cls.storage_backup: str = Env.to_str('STORAGE_BACKUP', cls.storage_backup)
        