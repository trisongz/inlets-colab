import typer
from typing import List, Optional
from typer import Argument, Option
from pathlib import Path
from lazycls.envs import Env
from lazycls.serializers import Yaml, OrJson
from inletscolab.client import InletsColab, logger

def parse_args(args: List[str] = []):
    kwargs = {}
    for arg in args:
        key, val = arg.split('=', 1)
        kwargs[key.strip()] = val.strip()
    return kwargs

def set_envs_from_args(args: List[str] = [], override: bool = False):
    envars = parse_args(args)
    for k,v in envars.items():
        Env.set_env(k, v, override=override)
    
def get_server_config():
    p = Path('/root/.config/code-server/config.yaml')
    if not p.exists(): return {}
    return Yaml.loads(p.read_text())

def load_envfile_config(envfile: Path, override: bool = False):
    envars = Yaml.loads(envfile.read_text()) if envfile.suffix in {'.yml', '.yaml'} else OrJson.loads(envfile.read_text())
    for k,v in envars.items():
        Env.set_env(k, v, override=override)
    

cli = typer.Typer()

@cli.command('start')
def run_inlets_colab(
    envfile: Optional[Path] = Option(None, help="Path to Env File that will be loaded"),
    encoded_envfile: bool = Option(False, help="Set to True if this Envfile is Encoded by using InletsColab.save()"),
    license: Optional[str] = Option(None, help="Inlets Pro License", envvar="INLETS_LICENSE"),
    overwrite_license: bool = Option(False, help="Whether to overwrite existing License"), 
    inlets_service: bool = Option(False, help="Whether to run Inlets as a systemd service - has failed testing."),
    server_background: bool = Option(False, help="Whether to run Server as a background service - has failed testing"),
    env: Optional[List[str]] = Option([], help = "A Repeating List of Envs in format of key=value"),
    override_env: bool = Option(False, help="Override existing Env Values"),
    inlet: Optional[List[str]] = Option([], help = "A Repeating List of Args for Inlets in format of key=value"),
    server:  Optional[List[str]] = Option([], help = "A Repeating List of Args for Server in format of key=value"),
    storage: Optional[List[str]] = Option([], help = "A Repeating List of Args for Storage in format of key=value"),
):  
    if envfile and envfile.exists():
        if encoded_envfile: InletsColab.load(path=envfile, override=override_env)
        else: load_envfile_config(envfile, override=override_env)  
        InletsColab.reload_from_env()
    if env:
        set_envs_from_args(env, override=override_env)
        InletsColab.reload_from_env()
    inlets_args = parse_args(inlet)
    server_args = parse_args(server)
    storage_args = parse_args(storage)
    InletsColab.start(license = license, overwrite_license= overwrite_license, inlets_service = inlets_service, server_background = server_background, inlets_args = inlets_args, server_args = server_args, storage_args = storage_args)

@cli.command('stop')
def stop_inlets_colab():
    InletsColab.stop()

serverCli = typer.Typer(name='server')

@serverCli.command('password')
def show_server_password():
    cfg = get_server_config()
    pw = cfg.get('password', 'None')
    logger.info(f'\nServer Password: {pw}\n')


cli.add_typer(serverCli)
