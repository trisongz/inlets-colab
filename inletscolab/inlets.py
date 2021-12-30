from lazycls.utils import exec_shell, exec_daemon, subprocess
from inletscolab.config import InletsConfig, logger, DebugEnabled

class Inlets:
    d: subprocess.Popen = None
    svc: bool = False

    @classmethod
    def run_startup(cls, license: str = None, overwrite_license: bool = False, **kwargs):
        InletsConfig.update_config(**kwargs)
        InletsConfig.ensure_inlets()
        InletsConfig.create_license(license=license, overwrite=overwrite_license)

    @classmethod
    def run_server(cls, license: str = None, overwrite_license: bool = False, **kwargs):
        cls.svc = False
        cls.run_startup(license = license, overwrite_license = overwrite_license, **kwargs)
        cmd = InletsConfig.get_cmd()
        if DebugEnabled: logger.info(cmd)
        cls.d = exec_daemon(cmd=cmd.split(' '), set_proc_uid=False)
        InletsConfig.display_info()
    
    @classmethod
    def kill_server(cls):
        if not cls.d: return
        cls.d.kill()
        cls.d = None

    @classmethod
    def create_service(cls, overwrite: bool = False):
        """ Creates a systemd service """
        if InletsConfig.systemd_path.exists() and not overwrite: return
        cmd = InletsConfig.get_cmd()
        cmd += f" --generate systemd > {InletsConfig.systemd_path.string}"
        if DebugEnabled: logger.info(cmd)
        exec_shell(cmd)
    
    @classmethod
    def exec_service(cls, cmd: str):
        if not InletsConfig.systemd_path.exists(): return
        cmd = f'systemctl {cmd} inlets'
        if InletsConfig.use_sudo: cmd = 'sudo ' + cmd
        if DebugEnabled: logger.info(cmd)
        exec_shell(cmd)
    
    @classmethod
    def enable_service(cls):
        return cls.exec_service('enable')
        
    @classmethod
    def disable_service(cls):
        return cls.exec_service('disable')

    @classmethod
    def start_service(cls):
        return cls.exec_service('start')
    
    @classmethod
    def stop_service(cls):
        return cls.exec_service('stop')
    
    @classmethod
    def restart_service(cls):
        return cls.exec_service('restart')
    
    @classmethod
    def reload_service(cls):
        return cls.exec_service('reload')

    @classmethod
    def run_service(cls, license: str = None, overwrite_license: bool = False, overwrite_service: bool = False, **kwargs):
        """ Runs all the processes to start the serice """
        cls.svc = True
        cls.run_startup(license = license, overwrite_license = overwrite_license, **kwargs)
        cls.create_service(overwrite= overwrite_service)
        cls.enable_service()
        cls.start_service()
        InletsConfig.display_info()

    @classmethod
    def kill_service(cls, disable: bool = True):
        r = cls.stop_service()
        if disable: cls.disable_service()
        return r

    @classmethod
    def kill(cls):
        if cls.svc: return cls.kill_service()
        return cls.kill_server()




