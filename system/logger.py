from genericpath import exists
import logging
from pathlib import Path
from typing import Optional


class Gamelogger:   # 游戏日志管理器
    def __init__(self,log_dir: str = 'logs',log_to_console: bool = False):   # 选择性输入控制台
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok = True)

        # 创建日志器
        self.logger = logging.getLogger("game")
        self.logger.setLevel(logging.DEBUG)

        # 判定是否实例化，若没有处理器Handler才继续
        if self.logger.hasHandlers():
            return

        # 战斗日志（INFO级别）
        gamerun_handler = logging.FileHandler(
            self.log_dir / "gamerun.log", 
            encoding='utf-8'
        )
        gamerun_handler.setLevel(logging.INFO)
        gamerun_handler.setFormatter(self._get_formatter())
        
        # 错误日志（ERROR级别）
        error_handler = logging.FileHandler(
            self.log_dir / "errors.log", 
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self._get_formatter())
        
            # 控制台（DEBUG级别）
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(self._get_formatter())
            self.logger.addHandler(console_handler)
        
        # 创建处理器
        self.logger.addHandler(gamerun_handler)
        self.logger.addHandler(error_handler)



    def _get_formatter(self) -> logging.Formatter:
        return logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def error(self, message: str, exc_info: bool = False) -> None:  # 报错
        self.logger.error(message, exc_info=exc_info)

    def gamerun(self, message: str) -> None:     # 游戏运行、回合信息
        self.logger.info(f"[gamerun] {message}")
    def info(self,message: str) -> None:         # 技能选择、执行
        self.logger.info(f"[info] {message}")      
    def debug(self, message: str) -> None:       # 伤害、数值变化中间值
        self.logger.debug(f"[debug] {message}")
    def warning(self, message: str) -> None:     # 数据缺失、异常
        self.logger.warning(f"[warning] {message}")
    