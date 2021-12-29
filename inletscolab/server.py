from .config import ServerConfig, logger
from lazycls.utils import exec_shell, exec_run, exec_daemon, subprocess
from lazycls.prop import classproperty


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
    def run_background(cls, cmd: str):
        if cls.d: return
        cls.d = exec_daemon(cmd=cmd)

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
        if ServerConfig.mount_drive and ServerConfig.is_colab:
            from google.colab import drive
            drive.mount("/content/drive")
        if ServerConfig.code: ServerConfig.ensure_codeserver()
    
    @classmethod
    def run_server(cls, background: bool = True, **kwargs):
        cls.run_startup(**kwargs)
        cmd = ServerConfig.get_cmd()
        logger.info(cmd)
        if not background: return cls.run_foreground(cmd)
        cls.run_background(cmd)
        ServerConfig.display_info()



            
        
             
    

    
    
        