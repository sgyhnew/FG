from __future__ import annotations
from ast import Tuple
from re import I
from typing import TYPE_CHECKING, Callable, Optional,Tuple
if TYPE_CHECKING:
    from FG.main import Game
from multiprocessing import set_forkserver_preload
import sys
from pathlib import Path
from FG.constants import *
from FG.constants import GameResult as GR
from FG.constants import AttributeEvent as AE
from func import say, load_json

DamageResult = Tuple[int, Optional[AE]]  # 定义伤害结果返回的类型

class MpConfig: #   mp管理规则
    MP_RULES = {
        GR.ROUND: 1,
        GR.COMBAT_WIN: 3,
        GR.COMBAT_DRAW: 1,
        GR.DEFENSE_TURN: 2,
    }

class Attribute:    # 内部类属性系统，负责战斗中状态展示
    def __init__(self,game:Game):
        self.game = game
        self.hp1 = 100  # player
        self.hp2 = 100  # pc
        self.hp1_top = 100  # 玩家血量上限
        self.hp2_top = 100  # 对手血量上限
        self._mp_player = 20  # 玩家能量 
        self._mp_pc = 0       # PC能量（FG2.0时移除）
        self.mp_player_top = 100    # 能量上限
        self.mp_pc_top = 50         # PC能量上限较低，为移除做铺垫

    def attribute_desc(self): # 状态描述
        
        player_mp = self.mp_get(True)
        pc_mp = self.mp_get(False)
        print(f"{'='*40}")
        print(f"  ❤️  玩家血量: {self.hp1:>3}/100  |  ⚔️  能量: {player_mp:>2}/{self.mp_player_top}")
        print(f"  💀 对手血量: {self.hp2:>3}/100  |  🛡️  能量: {pc_mp:>2}/{self.mp_pc_top}")
        print(f"{'='*40}")

    def hp_get(self, is_player:bool) -> int: # 血量的调用
        return self.hp1 if is_player else self.hp2
    def hp_set(self, is_player:bool, value:int ) -> int: # 血量的设置

        top_hp = self.hp1_top if is_player else self.hp2_top
        new_val = max(0,min(value,top_hp))  # 限制血量在0~上限之间

        return new_val

    def mp_get(self, is_player:bool) -> int: # 能量的调用
        return self._mp_player if is_player else self._mp_pc
    def mp_set(self, is_player:bool, value): # 能量的设置
        attr = '_mp_player' if is_player else '_mp_pc'
        attr_top = 'mp_player_top' if is_player else 'mp_pc_top'
        top = getattr(self,attr_top)
        new_val = max(0,min(value,top))
        setattr(self, attr, new_val)
        return new_val
    def _mp_delta(self, reason: int | str | GR) -> int:   # 根据原因获取能量变化值
        # case1：GR枚举的 .value 属性
        if isinstance(reason, GR):
            return MpConfig.MP_RULES.get(reason,0)
    
        # case2：整数（如消耗能量 -cost）
        # 必须放在字符串判断之前，因为字符串也有 .isdigit 方法
        if isinstance(reason, int):
            return reason
        
        # case3：字符串映射（兼容旧代码）
        if isinstance(reason, str):
            try:
                # 将字符串转化为GR枚举
                enum_member = getattr(GR,reason.upper())
                return MpConfig.MP_RULES.get(enum_member, 0)
            except AttributeError:
                print(f"[警告] 未知的能量原因字符串: '{reason}'")
                return 0
        
        # case4：无法解析
        print(f"[警告] 无法解析能量变化: {reason} (类型: {type(reason).__name__})")
        return 0
    def mp_do(self, is_player: bool ,reason: GR | str | int) -> int:   # 战斗中能量的获取
        # 根据原因调整能量,支持三种输入

        delta = self._mp_delta(reason)
        
        current = self.mp_get(is_player)
        new_value = current + delta
        return self.mp_set(is_player, new_value)
    
    def damage_take(self,   # 伤害处理
            play_damage: int,   # 玩家伤害
            pc_damage: int,     # 对方伤害 
            ) -> DamageResult:   
        # case1: 获取当前血量
        play_current_hp = self.hp_get(True) 
        pc_current_hp = self.hp_get(False)

        # case2: 计算新的血量
        play_hp = max(0,play_current_hp - play_damage)    
        pc_hp = max(0,pc_current_hp - pc_damage)

        # case3: 设置新的血量
        self.hp1 = self.hp_set(True, play_hp)
        self.hp2 = self.hp_set(False, pc_hp)
        # # case4: 判断血量事件
        # hp_event: Optional[AE] = None      
        # hp_top = self.hp1_top if 

        # if   hp == 0:
        #     hp_event = AE.DEATH
        # elif hp <= hp_top * 0.2:
        #     hp_event = AE.FATAL
        # elif hp <= hp_top * 0.5:
        #     hp_event = AE.CRITICAL
        # elif hp < current_hp:
        #     hp_event = AE.HURT

        # # case2：触发额外受伤事件
        # if is_player and damage > 20:
        #     print("对方招式精湛，你血流如注！")
        return None
# if __name__ == '__main__':
