from inletscolab.config import ServerConfig, logger, DebugEnabled
from lazycls.utils import exec_shell, exec_daemon, subprocess


class Server:
    d: subprocess.Popen = None

    @classmethod
    def run_foreground(cls, cmd: str):
        if cls.d: return
        cls.d = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True)
        with cls.d as proc:
            for line in proc.stdout:
                print(line, end="")
    
    @classmethod
    def run_background(cls, cmd: str, set_proc_uid: bool = False, **kwargs):
        if cls.d: return
        cls.d = exec_daemon(cmd=cmd.split(' '), set_proc_uid=set_proc_uid, **kwargs)

    @classmethod
    def kill(cls):
        if not cls.d: return
        cls.d.kill()
        cls.d = None

    @classmethod
    def run_startup(cls, **kwargs):
        if cls.d: return
        ServerConfig.update_config(**kwargs)
        exec_shell(f"fuser -n tcp -k {ServerConfig.port}")
        if ServerConfig.code: ServerConfig.ensure_codeserver()
    
    @classmethod
    def run_server(cls, background: bool = True, **kwargs):
        cls.run_startup(**kwargs)
        cmd = ServerConfig.get_cmd()
        if DebugEnabled: logger.info(cmd)
        ServerConfig.display_info()
        if not background: return cls.run_foreground(cmd)
        cls.run_background(cmd, **kwargs)
        



            
        
             
    

    
    
        