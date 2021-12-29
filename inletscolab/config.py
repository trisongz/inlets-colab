from uuid import uuid1
from lazycls.envs import Env
from lazycls.prop import classproperty
from lazycls.types import *
from lazycls.io import Path
from lazycls.serializers import Base
from lazycls.utils import find_binary_in_path, exec_shell, exec_run, exec_daemon, subprocess
from logz import get_cls_logger, get_logger

try:
    from google.colab import drive
    colab_env = True
except ImportError:
    colab_env = False


root_dir = Path.get_parent_path(__file__)

bin_dir = root_dir.joinpath('bin')
scripts_dir = root_dir.joinpath('scripts')
user_exec_dir = Path('/usr/local/bin')

_inlets_installer = scripts_dir.joinpath('get_inlets.sh')
_inlets_exec = user_exec_dir.joinpath('inletsctl')

_cs_installer = scripts_dir.joinpath('get_codeserver.sh')

CSDefaultExtensions = ["ms-python.python", "ms-toolsai.jupyter", "mechatroner.rainbow-csv", "vscode-icons-team.vscode-icons"]
CSDefaultVersion = "3.10.2"

logger = get_logger('inlets-colab')

class InletsConfig:
    license: str = Env.to_str('INLETS_LICENSE', '')
    token: str = Env.to_str('INLETS_TOKEN', '')
    server_host: str = Env.to_str('INLETS_SERVER_HOST', '')
    server_port: int = Env.to_int('INLETS_SERVER_PORT', 8123)
    client_host: str = Env.to_str('INLETS_CLIENT_HOST', 'localhost')
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
        return Path.get_path('/content/.inlets', True)

    @classproperty
    def lincense_file(cls):
        cls.inlets_dir.mkdir(parents=True, exist_ok=True)
        return cls.inlets_dir.joinpath('license')

    @classproperty
    def inlets_exists(cls):
        return _inlets_exec.exists()
    
    @classproperty
    def tunnel_url(cls):
        if cls.is_cluster: return f'wss://{cls.server_host}'
        return f'wss://{cls.server_host}:{cls.server_port}/connect'
    
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
        cmd = f'inlets-pro {cls.client_type} client --url {cls.tunnel_url}' 
        if cls.is_cluster:
            cmd += f' --upstream={cls.upstream} --port={cls.upstream_port} --auto-tls=false'
        else: 
            cmd += f' --upstream={cls.upstream_url}'
    
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
        exec_shell(f'sudo bash {_inlets_installer.string}')
        exec_shell('sudo inletsctl download')
    
    @classmethod
    def display_info(cls):
        msg = "Inlets Client is Running at:\n"
        if cls.is_cluster:
            msg += f" {cls.server_host}"
        else: msg+= f" {cls.domain_name}"
        msg += f". Listening to: http://{cls.client_host}:{cls.client_port}"
        logger.info(msg)



class ServerConfig:
    extensions: List[str] = Env.to_list('CODESERVER_EXTENSIONS', CSDefaultExtensions)
    version: str = Env.to_str('CODESERVER_VERSION', CSDefaultVersion)
    authtoken: str = Env.to_str('SERVER_AUTHTOKEN', '')
    password: str = Env.to_str('SERVER_PASSWORD', '')
    mount_drive: bool = Env.to_bool('MOUNT_DRIVE')
    code: bool = Env.to_bool('RUN_CODE', 'true')
    lab: bool = Env.to_bool('RUN_LAB')
    generate_auth: bool = Env.to_bool('GENERATE_AUTH', 'true')

    @classmethod
    def update_config(cls, **kwargs):
        for k,v in kwargs.items():
            if getattr(cls, k, None): setattr(cls, k, v)

    @classproperty
    def cs_exists(cls):
        return find_binary_in_path('code-server')

    @classproperty
    def is_colab(cls):
        return colab_env
    
    @classmethod
    def ensure_codeserver(cls):
        if cls.cs_exists or not cls.is_colab: return
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

    @classmethod
    def get_lab_cmd(cls):
        cmd = "jupyter-lab --ip='localhost' --allow-root --ServerApp.allow_remote_access=True --no-browser"
        token = cls.get_lab_token()
        password = cls.get_lab_password()
        if password:
            cmd += f" --ServerApp.token='{token}' --ServerApp.password='{password}' --port {cls.port}"
        else:
            cmd += f" --ServerApp.token='{token}' --ServerApp.password='' --port {cls.port}"
        return cmd

    @classmethod
    def get_codeserver_cmd(cls):
        password = cls.get_code_password()
        if password: return f"PASSWORD={password} code-server --port {cls.port} --disable-telemetry"
        return f"code-server --port {cls.port} --auth none --disable-telemetry"
        
    @classmethod
    def get_cmd(cls):
        if cls.code: return cls.get_codeserver_cmd()
        return cls.get_lab_cmd()

    @classmethod
    def display_info(cls):
        msg = "Running: "
        if cls.code:
            msg += "Code Server"
        elif cls.lab:
            msg += "Jupyter Lab"
        msg += f" @ localhost:{cls.port}"
        logger.info(msg)