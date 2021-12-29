from .config import logger, classproperty
from .inlets import Inlets
from .server import Server

""" Wrapper Class to manage both"""
class InletsColab:

    @classmethod
    def start(cls, license: str = None, overwrite_license: bool = False, overwrite_service: bool = False, inlets_service: bool = False, server_background: bool = False, **kwargs):
        if inlets_service: Inlets.run_service(license = license, overwrite_license= overwrite_license, overwrite_service= overwrite_service, **kwargs)
        else: Inlets.run_server(license = license, overwrite_license= overwrite_license)
        Server.run_server(background=server_background, **kwargs)
    
    @classmethod
    def stop(cls):
        Server.kill()
        Inlets.kill()

        

