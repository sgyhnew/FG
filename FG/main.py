# -*- coding: utf-8 -*-
import sys
from pathlib import Path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from functools import lru_cache
from typing import Dict, Any, Callable, Iterator, Tuple
from dataclasses import dataclass
from system.attribute import Attribute
from system.menu import Menu
from system.combat import Combat, CombatData
from system.skill import SkillData, SkillManager
from system.logger import Gamelogger
from constants import *
from constants import GamePhase as GP
from func import say, load_json

class Game:
    __slots__ = (
        'menu','attribute','combat','logger','skill',  # 外部类的调用
        'count','beats',              # 战斗相关变量
        'skill','action',             # 动作,为日后其他版本迭代做准备
    )   
    def __init__(self): # 变量的声明和方法的使用
        self.attribute = Attribute(self)
        self.menu = Menu(self)
        self.combat = Combat(self)
        self.logger = Gamelogger(log_dir='logs')
        self.skill = SkillManager()
        self.beats = BEATS_MAP
        self.count = 0

        self.logger.info("战斗系统初始化完成")  # 初始化


    def fight(self, player_skill: str): # 回合制战斗
  
        """Game类只负责调用战斗系统和处理结果"""
        result: CombatData= self.combat.combat_turn(player_skill)
        
        # 根据结果触发额外逻辑
        if result.damage_to_player > 20:    # 重伤提示
            say("这一击让你气血翻涌！")
        return True
    
    def main(self): # 主程序入口,回合外的、宏观的 交互战斗流程
        while 1:
            
            # 进入新回合
            self.count +=1
            print(f"第{self.count}回合")

            # 对方HP<50第一次判定
            if self.attribute.hp2 > 50:
                say("对方覆手而立，侧视而笑：'阁下出招吧，拳、剑、刀皆可，若有疑惑我自可欣然解答。若是不愿再战，逃走即可！'\n")
            else:
                say("对方全身紧绷，紧紧盯住你一举一动'阁下好身手，我们今日到此为止如何？'\n")
            self.attribute.attribute_desc()   # 展示血量
            # self.menu.debug_state() # debug
            menu_result = self.menu.run()     # 实例化菜单栈

            # 菜单选项
            if menu_result is None:
                # 正常返回，继续下一回合
                continue

            elif menu_result == '__exit__':  # 退出，其余关键字的触发在menu中，exit则是为了退出main中的主循环
                break
            elif isinstance(menu_result, str):
                # 攻击技能选择
                skill_name = menu_result
                try:
                    skill_data = self.skill.get_skill(skill_name)
                    cost = skill_data.cost
                    
                    # 检查能量是否足够
                    if self.attribute.mp_get(True) >= cost:
                        self.attribute.mp_do(True, -cost)
                        self.fight(skill_name)
                    else:
                        say(f"能量不足{cost}点，无法施展{skill_name}！")
                        
                except KeyError:
                    say(f"技能'{skill_name}'数据异常，无法使用")
            elif isinstance(menu_result, int):
                # 防御等级选择
                defense_level = menu_result
                try:
                    # 根据防御等级获取对应的防御技能
                    defense_skill_name = "进阶防御" if defense_level >= 2 else "基础防御"
                    skill_data = self.skill.get_skill(defense_skill_name)
                    cost = skill_data.cost
                    
                    # 检查能量是否足够
                    if self.attribute.mp_get(True) >= cost:
                        self.attribute.mp_do(True, -cost)
                        self.fight(skill_name)
                    else:
                        say(f"能量不足{cost}点，无法进行防御！")
                        
                except KeyError:
                    say("防御技能数据异常")
            else:
                print("此招式你尚未习得，思虑再三决定重新出招")

if __name__ == "__main__":
        game = Game()
        game.main() 