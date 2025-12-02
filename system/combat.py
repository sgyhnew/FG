# -*- coding: utf-8 -*-
from __future__ import annotations
from tarfile import data_filter
from tkinter import ROUND
from turtle import Turtle
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from FG.main import Game
from logging import Logger
from dataclasses import dataclass,field
import random
from time import sleep
from FG.constants import *
from FG.constants import PriorityLevel as PL
from FG.constants import GameResult as GR
from FG.constants import FightPhase as FP
from FG.constants import AttributeEvent as AE
from func import say
from system.attribute import Attribute,MpConfig,DamageResult
from system.logger import Gamelogger
from system.skill import SkillData,DefenseSkill,SkillManager
@dataclass(frozen=True)  # 冻结类
class CombatData:    # 战斗结果数据
    damage_to_player: int   # 玩家受到的伤害
    damage_to_pc: int       # PC受到的伤害
    desc: str        # 效果描述
@dataclass
class CombatContext:  # 战斗数据上下文
    player_skill: SkillData | None = None  # 玩家技能
    pc_skill: SkillData | None = None      # pc技能
    player_input: str | None = None # 原始输入（仅用于日志，不参与逻辑）
    combat_data: CombatData | None = None      # 结果（由结算阶段写入）
    
class Combat:  # 战斗系统 

    def __init__(self, game: Game):
        self.game = game
        self.attribute = game.attribute
        self.skill = SkillManager()
        self.logger = Gamelogger(log_dir='logs')
    def _phase_prepare(self, context: CombatContext):        # 准备阶段
        self.logger.gamerun(f"第{self.game.count}回合准备阶段")
        say(f"【{FP.PREPARE.value}】",SAY_SPEED)
        try:
            # case 1：存活判定
            if not self.is_alive(True):
                say("\n【战斗结束】你重伤倒地,无法继续战斗...")
                print("对方拱手道：'承让了！'")
            if not self.is_alive(False):
                say("\n【战斗结束】对方口吐鲜血,单膝跪地...")
                print("对方喘息道：'阁下武功高强，在下佩服！'")
                

            # case 2：能量事件
            self.logger.gamerun(f"因{GR.ROUND},玩家MP +{MpConfig.MP_RULES.get(ROUND)}, PC MP +{MpConfig.MP_RULES.get(ROUND)}")
            self.attribute.mp_do(True, GR.ROUND)
            self.attribute.mp_do(False, GR.ROUND)
        except:
            self.logger.error("战斗准备阶段异常")
            raise
        return None
    def _phase_player_action(self, context: CombatContext):  # 玩家行动阶段
        self.logger.debug(f"第{self.game.count}回合玩家行动阶段: input={context.player_input}, skill={context.player_skill}")
        say(f"【{FP.ACTION_PLAYER.value}】",SAY_SPEED)
        try:
            self.logger.info(f"玩家选择{context.player_skill.category}:{context.player_skill.name}")
            self._build_effect('你',context.player_skill.name) # 传入技能对象
            self.attribute.mp_do(True, GR.DEFENSE_TURN) if isinstance(context.player_skill,DefenseSkill) else None
        except:
            self.logger.error("玩家行动阶段异常")
    def _phase_pc_action(self, context: CombatContext):      # 对手行动阶段
        self.logger.gamerun(f"第{self.game.count}回合PC行动阶段")
        say(f"【{FP.ACTION_PC.value}】",SAY_SPEED)
        try:
            self._build_effect('对方',context.pc_skill.name)
        except:
            self.logger.error("PC行动阶段异常")
    def _phase_resolve(self,context: CombatContext):         # 结算阶段
        self.logger.gamerun(f"第{self.game.count}回合结算阶段")
        say(f"【{FP.RESOLVE.value}】",SAY_SPEED)
        try:
            context.combat_data = self.judge(context.player_skill, context.pc_skill)
            print(f"{context.combat_data.desc}")
        except Exception as e:
            self.logger.error("战斗结算阶段异常")
            raise e
        
    def is_alive(self,character: str | True | False | None = None) -> bool:  # 判断存活和胜负 同时为0判玩家为失败
        if character == "player" or character == True:
            return True if self.attribute.hp1 > 0 else False
        if character == "pc" or character == False:
            return True if self.attribute.hp1 <= 0 or self.attribute.hp2 > 0 else False
        if character == None:
            return True if self.attribute.hp1 > 0 and self.attribute.hp2 <= 0 else False
    def is_counter(self,attacker_skill: str, target_skill: str) -> bool:  # 判断是否克制
        return True if BEATS_MAP.get(attacker_skill) == target_skill else False

    def _choose_pc_skill(self) -> str:                          # pc技能选择逻辑
        current_hp = self.attribute.hp2
        max_hp = getattr(self.attribute, 'hp2_top', 100)
        hp_percentage = current_hp / max_hp

        # 血量高于50%，随机选择lv1攻击技能
        if hp_percentage > 0.5:
            return self._get_random_attack_skill_by_level("lv1")
        if hp_percentage > 0.25:
            return self._get_random_attack_skill_by_level("lv2")
        else:
            # 留余
            return self._get_random_attack_skill_by_level("lv2")   # 当前默认用lv2
    def _get_random_attack_skill_by_level(self, target_level: str) -> str:  # 在指定等级中随机选1个攻击技能
        """基于基础接口构建：在指定等级中随机选1个攻击技能"""
        # 获取所有技能名称
        all_skill_names = list(self.skill._skill_cache.keys())
        
        # 过滤出指定等级的攻击技能
        attack_skills = [
            name for name in all_skill_names
            if (self.skill.get_skill(name).category == "attack" and 
                self.skill.get_skill(name).level == target_level)
        ]
        
        if attack_skills:
            return random.choice(attack_skills)
        
        # 保底机制
        print(f"[警告] 等级 '{target_level}' 没有找到攻击技能，使用默认技能")
        return "基础拳"
    
    def _damage_apply(self,        # 伤害应用,无返回
            player_damage: int,   # 玩家伤害
            pc_damage: int,       # 伤害值
        ) -> None:  
        # case1: 调用伤害处理
        self.attribute.damage_take(player_damage,pc_damage)
        # # case2: 检查事件，输出日志(view层职责)
        # if event == AE.DEATH:
        #     self.logger.gamerun(f"{target_name}受到了 {damage} 点伤害，生命值归零！")
        # elif event == AE.FATAL:
        #     self.logger.gamerun(f"{target_name}受到了 {damage} 点伤害。他受了致命伤！")
        # elif event == AE.CRITICAL:
        #     self.logger.gamerun(f"{target_name}受到了 {damage} 点伤害。他受到大量伤害。")
        # elif event == AE.HURT:
        #     self.logger.gamerun(f"{target_name}受到了 {damage} 点伤害。")
  
        return None
    def _damage_calculate(self,    # 伤害计算,返回双方伤害值 
            player_skill: SkillData,      # 玩家技能
            pc_skill: SkillData           # 对方技能
        ) -> tuple[int, int]:
        # case 1：获取基础伤害(技能没有伤害则默认0)
        try:
            player_skill_damage =getattr(player_skill, 'damage', 0)
            pc_skill_damage = getattr(pc_skill, 'damage', 0)
        except Exception as e:
            self.logger.error("伤害计算阶段异常")
            raise e
        # case 2：应用防御减免
        try:
            player_reduction = getattr(player_skill, 'damage_reduction',0)
            pc_reducition = getattr(pc_skill, 'damage_reduction', 0)
        except:
            self.logger.error("防御减免阶段异常")
        # case 3: 计算最终伤害，并设定安全值最小1点
        try:
            player_damage = max(1, player_skill_damage - pc_reducition)
            pc_damage = max(1, pc_skill_damage - player_reduction)
        except:
            self.logger.error("最终伤害计算阶段异常")
        # case 4: 最终伤害,现阶段唯有招式克制可叠加
        if self.is_counter(player_skill.name, pc_skill.name):
            player_damage *= 1.5
        if self.is_counter(pc_skill.name, player_skill.name):
            pc_damage *= 1.5
        
        return player_damage, pc_damage
    
    def _build_result(self, context: CombatContext) -> CombatData:  # 优先级结果构建
        """根据上下文构建最终结果"""
        pc_damage = getattr(context.pc_skill, 'damage', 0)
        player_damage = getattr(context.player_skill, 'damage', 0)
        # 判断胜负
        if pc_damage ==0:
            result_type = "defense"
            result_text = "你全力防御，化解了攻势！"
            winner = None
        elif player_damage == pc_damage:
            result_type = "draw"
            result_text = "双方虚招试探，未分胜负！"
            winner = None
        elif pc_damage < player_damage:
            result_type = "win"
            result_text = "你的攻势更凌厉！"
            winner = "player"
        elif pc_damage > player_damage:
            result_type = "lose"
            result_text = "对方招式老辣，你落得下风！"
            winner = "pc"
        else:
            result_type = "normal"
            result_text = "双方招式不相上下，难分高下！"
            winner = None
        
        # 能量更新
        if result_type == "draw":
            self.attribute.mp_do(True, GR.COMBAT_DRAW)
            self.attribute.mp_do(False, GR.COMBAT_DRAW)
        elif result_type == "win":
            self.attribute.mp_do(True, GR.COMBAT_WIN)
        elif result_type == "lose":
            self.attribute.mp_do(False, GR.COMBAT_WIN)
        
        # 构建描述文本
        defense_info = ""
        if isinstance(context.player_skill, DefenseSkill):
            defense_info = f" [你使用了{context.player_skill.name}]"
            desc = f"你施展【{context.player_skill.name}】，成功防御了对方的攻击，受到{pc_damage}点伤害"
        desc = f"{result_text}{defense_info} (你受{pc_damage}伤，对手受{player_damage}伤)"
        
        # # 调试日志
        # print("\n[优先级执行日志]", " → ".join(context.result_log))
        
        return CombatData(damage_to_player=pc_damage, damage_to_pc=pc_damage, desc = desc)

    def _build_effect(self, sub: str, skill: str):   # 技能效果
        print(sub,end="")
        try:
            print(self.skill.get_skill(skill).effect)
        except:
            print("技能效果构建失败")
        sleep(0.1 * SAY_SPEED)
    
    def combat_turn(self, player_skill: str) -> CombatData:   # 执行一个战斗回合
   
        context = CombatContext()
        pc_skill = self._choose_pc_skill()
        context.pc_skill = self.skill.get_skill(pc_skill)
        context.player_skill = self.skill.get_skill(player_skill)

        # case2: 执行战斗阶段
        try:
            self._phase_prepare(context)        # 准备阶段
            self._phase_player_action(context)  # 玩家行动阶段
            self._phase_pc_action(context)      # 对手行动阶段
            self._phase_resolve(context)        # 结算阶段
            if context.combat_data is None:
                self.logger.error("combat_data 未被设置，返回默认值")
                return CombatData(0, 0, "【错误】战斗数据未生成")
            return context.combat_data or CombatData(0, 0, "回合结束")
            
        except Exception as e:
            print(f"[战斗系统错误] {e}")
            return CombatData(0, 0, f"战斗异常: {e}")

    def judge(self,         # 战斗判断,传入双方技能，返回结果
              player_skill: SkillData, 
              pc_skill: SkillData,
              ) -> CombatData: 
        """
        纯计算服务：按优先级顺序执行双方技能，返回战斗结果
        不直接修改状态，只负责判断
        """
        # case 1：构建上下文
        try:
            context = CombatContext(
                player_skill=player_skill, 
                pc_skill=pc_skill,
                )
        except:
            self.logger.error("上下文构建失败") 
            raise
        # 2. 按优先级排序（P1优先，同层按priority数字，玩家优先于PC）
        # 格式：(技能, 归属方) 用于后续日志记录
        try:
            skills_to_execute = sorted(
                [(player_skill, "player"), (pc_skill, "pc")],
                key=lambda x: (
                    x[0].priority_level.value,  # 先按层级（P1 < P2）
                    x[0].priority,              # 再按优先级数字（越小越前）
                    0 if x[1] == "player" else 1  # 最后按归属（玩家优先于PC）
                )
            )
        except:
            self.logger.error("技能排序失败")
            raise
        # 3. 依次执行技能效果（修改上下文）
        try:   
            for skill, owner in skills_to_execute:
                self.logger.debug(f"{owner}使用了攻击技能: {skill.name}")
        except:
            self.logger.error("技能执行失败")
            raise
        # 4. 计算伤害
        try:
            player_raw_damage,pc_raw_damage = self._damage_calculate(player_skill, pc_skill)
        except:
            self.logger.error("伤害计算失败")
            raise
        # 5. 应用伤害
        try:
            self._damage_apply(player_raw_damage, pc_raw_damage)
        except:
            self.logger.error("伤害应用失败")
            raise
        self.logger.debug("战斗结束")
        # 6. 构建并返回结果
        return self._build_result(context)
    
 