from lazycls.types import *
from lazycls.io import Path, PathLike
from lazycls.envs import Env

from inletscolab.config import logger, StorageConfig, ServerConfig, InletsConfig
from inletscolab.inlets import Inlets
from inletscolab.server import Server

""" Wrapper Client Class to manage all resources"""

class InletsColab:
    
    @classmethod
    def setup_storage(cls, **kwargs):
        return StorageConfig.setup_storage(**kwargs)
    
    @classmethod
    def start_inlets(cls, license: str = None, overwrite_license: bool = False, overwrite_service: bool = False, inlets_service: bool = False, **kwargs):
        if inlets_service: Inlets.run_service(license = license, overwrite_license= overwrite_license, overwrite_service= overwrite_service, **kwargs)
        else: Inlets.run_server(license = license, overwrite_license= overwrite_license, **kwargs)

    @classmethod
    def start_server(cls, background: bool = False, **kwargs):
        Server.run_server(background=background, **kwargs)
    
    @classmethod
    def kill_inlets(cls): return Inlets.kill()
    
    @classmethod
    def kill_server(cls): return Server.kill()

    @classmethod
    def start(cls, license: str = None, overwrite_license: bool = False, overwrite_service: bool = False, inlets_service: bool = False, server_background: bool = False, inlets_args: Dict[str, Any] = {}, server_args:  Dict[str, Any] = {}, storage_args: Dict[str, Any] = {}, **kwargs):
        cls.start_inlets(license = license, overwrite_license= overwrite_license, overwrite_service= overwrite_service, inlets_service=inlets_service, **inlets_args)
        cls.setup_storage(**storage_args)
        cls.start_server(background=server_background, **server_args)
    
    @classmethod
    def stop(cls):
        cls.kill_server()
        cls.kill_inlets()
        
    @classmethod
    def export_config(cls):
        data = {}
        data.update(**InletsConfig.export_config())
        data.update(**ServerConfig.export_config())
        data.update(**StorageConfig.export_config())
        return data
    
    @classmethod
    def save(cls, path: PathLike = '/content/inlets_colab.json', overwrite: bool = False):
        p = Path(path)
        if p.exists() and not overwrite:
            logger.error(f'InletsColab Config exists at {p.string} and overwrite = False. Exiting')
            return
        logger.info(f'Saving InletsColab Config to {p.string}')
        return Env.save_config(cls.export_config(), path=p)

    @classmethod
    def load(cls, path: PathLike = '/content/inlets_colab.json', override: bool = False):
        p = Path(path)
        logger.info(f'Loading InletsColab Config from {p.string}')
        p = Env.load_config(p, set_as_env=True, override=override)
        InletsConfig.reload_from_env()
        ServerConfig.reload_from_env()
        StorageConfig.reload_from_env()
    
    @classmethod
    def reload_from_env(cls):
        InletsConfig.reload_from_env()
        ServerConfig.reload_from_env()
        StorageConfig.reload_from_env()
    
        

