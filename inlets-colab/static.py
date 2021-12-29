from lazycls.io import Path
from lazycls.utils import find_binary_in_path
from lazycls.utils import exec_shell

root_dir = Path.get_parent_path(__file__)

bin_dir = root_dir.joinpath('bin')
scripts_dir = root_dir.joinpath('scripts')
user_exec_dir = Path('/usr/local/bin')

#_inlets_exec = bin_dir.joinpath('inletsctl')
_inlets_installer = scripts_dir.joinpath('get_inlets.sh')
_inlets_exec = user_exec_dir.joinpath('inletsctl')
_inlets_exists: bool = _inlets_exec.exists()

def ensure_inlets():
    if _inlets_exists: return
    exec_shell(f'cd {bin_dir.string} && sudo bash {_inlets_installer.string}')
    exec_shell('sudo inletsctl download')


#ensure_inlets()


