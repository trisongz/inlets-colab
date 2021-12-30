import typer
from typing import Tuple, List, Optional
from typer import Argument, Option
from .client import InletsColab

def parse_args(args: List[Tuple[str, str]]):
    kwargs = {}
    for arg in args:
        key, val = arg
        kwargs[key] = val
    return kwargs

cli = typer.Typer()

@cli.command('start')
def run_inlets_colab(
    license: str = Argument(None),
    overwrite_license: bool = Option(False), 
    overwrite_service: bool = Option(False), 
    inlets_service: bool = Option(False), 
    server_background: bool = Option(False), 
    inlet: Optional[List[Tuple[str, str]]] = Option((None, None), help = "A Repeating List of Args for Inlets"),
    server:  Optional[List[Tuple[str, str]]] = Option((None, None), help = "A Repeating List of Args for Server"),
    storage: Optional[List[Tuple[str, str]]] = Option((None, None), help = "A Repeating List of Args for Storage"),
):  
    inlets_args = parse_args(inlet)
    server_args = parse_args(server)
    storage_args = parse_args(storage)
    InletsColab.start(license = license, overwrite_license= overwrite_license, overwrite_service = overwrite_service, inlets_service = inlets_service, server_background = server_background, inlets_args = inlets_args, server_args = server_args, storage_args = storage_args)

@cli.command('stop')
def stop_inlets_colab():
    InletsColab.stop()
    
