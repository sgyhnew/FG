# -*- coding: utf-8 -*-
from __future__ import annotations
from tkinter import ROUND
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
@dataclass
class CombatData:        # 战斗结果数据类
    damage_to_player: int   # 玩家造成伤害
    damage_to_pc: int       # 对方造成伤害
    description: str        # 结果描述
@dataclass
class CombatContext:     # 战斗执行上下文
    player_skill: SkillData | None # 玩家技能
    pc_skill: SkillData | None     # 对方技能
    defense_skill: DefenseSkill | None = None
    skip_damage: bool = False      # 是否跳过伤害结算
    player_damage: int = 0         # 玩家已受伤害值
    pc_damage: int = 0             # PC已受伤害值
@dataclass
class PhaseContext:      # 阶段回合上下文
    player_input:  str | None
    defense_skill: DefenseSkill | None
    player_skill:  SkillData | None = None
    pc_skill:      str | None = None
    combat_data: CombatData | None = None

class Combat:  # 战斗系统 

    def __init__(self, game: Game):
        self.game = game
        self.attribute = game.attribute
        self.skill = SkillManager()
        self.logger = Gamelogger(log_dir='logs')
    def _phase_prepare(self, context: PhaseContext):        # 准备阶段
        self.logger.gamerun(f"第{self.game.count}回合准备阶段")
        say(f"【{FP.PREPARE.value}】",SAY_SPEED)
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
        return None
    def _phase_player_action(self, context: PhaseContext):  # 玩家行动阶段
        self.logger.debug(f"玩家行动阶段: input={context.player_input}, defense={context.defense_skill}")
        say(f"【{FP.ACTION_PLAYER.value}】",SAY_SPEED)

        # case1: 防御选择
        if context.defense_skill:
            context.player_skill = None
            self.logger.info(f"玩家选择防御: {context.defense_skill.name}")
            self._execute_defense(context.defense_skill)    # 传入技能对象
        # case2: 攻击选择
        if context.player_input:
            self._execute_effect(context.player_input, "你")
            context.player_skill = context.player_input
            self.logger.info(f"玩家使用技能: {context.player_input}")
    def _phase_pc_action(self, context: PhaseContext):      # 对手行动阶段
        self.logger.gamerun("PC行动阶段")
        say(f"【{FP.ACTION_PC.value}】",SAY_SPEED)

        context.pc_skill = self._choose_pc_skill()
        self._execute_effect(context.pc_skill, "对手")
    def _phase_resolve(self,context: PhaseContext):         # 结算阶段
        say(f"【{FP.RESOLVE.value}】",SAY_SPEED)

        # case1: 防御选择
        if context.defense_skill:
            damage = self._damage_calculate(    # 计算伤害
                context.pc_skill,       # PC攻击
                context.defense_skill,  # 防御技能
                False                   # 防御回合无克制
        )
            damage = self._damage_apply(        # 应用伤害
                target_is_player=True,      # 受击方是玩家
                damage=damage, 
                skill_name=context.pc_skill # 造成伤害的技能名
            )
            context.combat_data = self._build_defense_result(context.defense_skill,damage)
        # case2：攻击选择
        else:
            context.combat_data = self.judge(context.player_skill, context.pc_skill)
        print(f"{context.combat_data.description}")
 
    def is_alive(self, is_player):  # 胜负判定 同时为0判玩家为失败
        return self.attribute.hp1 > 0 if is_player else self.attribute.hp2 > 0

    def _execute_effect(self, skill_name: str, subject: str):   # 技能效果
        print(subject, end="")
        print(self.skill.get_skill(skill_name).effect) 
        sleep(0.1 * SAY_SPEED)

    def _execute_defense(self, defense_skill: DefenseSkill):    # 防御效果
        print("你", end="")
        print(defense_skill.effect) 
        self.attribute.mp_do(True, GR.DEFENSE_TURN)
        sleep(0.1 * SAY_SPEED)
   
    def _execute_skill_effect(self, skill: SkillData, owner: str, context: CombatContext):  # 战斗中技能效果的执行
        """在上下文中执行单个技能的效果"""
        
        # 执行技能效果（调用现有的effect函数）
        # 注意：现有effect不接受参数，所以暂时不改变effect签名
        # 后续可扩展为 effect(context)
        
        # 记录日志
        # context.result_log.append(f"[{'玩家' if owner == 'player' else '对手'}] {skill.name}")
        
        # 根据技能类型影响上下文
        if skill.category == "defense":
            # 防御效果：标记跳过伤害
            context.skip_damage = True
            # context.result_log.append(" → 防御姿态生效")
        # elif skill.category == "attack":
        #     # 攻击效果：如果已标记防御，记录被格挡
        #     if context.skip_damage:
        #         context.result_log.append(" → 攻击被防御格挡")
        #     else:
        #         context.result_log.append(" → 攻击准备就绪")

    def _build_defense_result(self, ddefense_skill: DefenseSkill, damage: int) -> CombatData: # 防御结果构建
        desc = f"你施展【{ddefense_skill.name}】，受到{damage}点伤害"
        return CombatData(damage, 0, desc)
    
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
    

    def _damage_apply(self,        # 伤害应用
            target_is_player: bool,      # 目标是玩家
            damage: int,                 # 伤害
            skill_name: str | None,      # 技能名
        ) -> int:  
        target_name = "你" if target_is_player else "对手"
        
        # case1: 调用伤害处理，并获取事件
        event = self.attribute.damage_take(target_is_player, damage, skill_name)
        # case2: 检查事件，输出日志(view层职责)
        if event == AE.DEATH:
            self.logger.gamerun(f"{target_name}受到了 {damage} 点伤害，生命值归零！")
        elif event == AE.FATAL:
            message = f"{target_name}受到了 {damage} 点伤害。他受了致命伤！"
            self.logger.gamerun(message)
        elif event == AE.CRITICAL:
            self.logger.gamerun(f"{target_name}受到了 {damage} 点伤害。他受到大量伤害。")
        elif event == AE.HURT:
            self.logger.gamerun(f"{target_name}受到了 {damage} 点伤害。")
  
        return damage

    def _damage_calculate(self,    # 伤害计算 
            attack_skill: str | None,      # 攻击方技能名（防御回合为None）
            defense_skill: DefenseSkill | None,      # 防御技能名
            is_countered: bool               # 是否被克制
        ) -> int:
        if attack_skill is None:
            return 0
        # case 1：获取基础伤害（防御回合用默认进阶/基础伤害）
        base_damage = self.skill.get_skill(attack_skill).damage
        
        # case 2：应用防御减免
        reduction = defense_skill.damage_reduction if defense_skill else 0
        
        # case 3: 计算最终伤害，并设定安全值最小1点
        damage = max(1, base_damage - reduction)
        
        # case 4: 最终伤害,现阶段唯有招式克制可叠加
        if is_countered:
            damage *= 2
        
        return damage
    
    def _build_priority_result(self, context: CombatContext) -> CombatData:  # 优先级结果构建
        """根据上下文构建最终结果"""
        # 判断胜负（基于是否被防御和伤害值）
        if context.skip_damage:
            result_type = "defense"
            result_text = "你全力防御，化解了攻势！"
            winner = None
        elif context.player_damage == context.pc_damage == 0:
            result_type = "draw"
            result_text = "双方虚招试探，未分胜负！"
            winner = None
        elif context.pc_damage > context.player_damage:
            result_type = "win"
            result_text = "你的攻势更凌厉！"
            winner = "player"
        elif context.pc_damage < context.player_damage:
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
        defense_info = f" [你使用了{context.defense_skill.name}]" if context.defense_skill else ""
        desc = f"{result_text}{defense_info} (你受{context.player_damage}伤，对手受{context.pc_damage}伤)"

        # # 调试日志
        # print("\n[优先级执行日志]", " → ".join(context.result_log))
        
        return CombatData(context.player_damage, context.pc_damage, desc)

    def combat_turn(self, player_input: str, defense_skill_name: str | None) -> CombatData:   # 执行一个战斗回合
        # 防御性检测，防御技能只能通过 defense_skill_name 传入
        if player_input and defense_skill_name:
            self.logger.warning("同时指定攻击和防御，忽略攻击")
            player_input = None

        defense_skill = None
        if defense_skill_name:
            skill = self.skill.get_skill(defense_skill_name)
            if isinstance(skill, DefenseSkill):
                defense_skill = skill
            else:
                raise ValueError(f"技能 '{defense_skill_name}' 不是防御技能")

        context = PhaseContext(player_input, defense_skill)
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

    def judge(self,         # 战斗判断
              player_skill_name: str, 
              pc_skill_name: str,
              defense_skill: DefenseSkill | None = None
              ) -> CombatData: 
        """
        纯计算服务：按优先级顺序执行双方技能，返回战斗结果
        不直接修改状态，只负责判断
        """
        # case 1：获取技能元数据
        player_skill = self.skill.get_skill(player_skill_name)
        pc_skill = self.skill.get_skill(pc_skill_name)
        
        # case 2：传入防御技能
        context = CombatContext(
            player_skill=player_skill, 
            pc_skill=pc_skill,
            defense_skill=defense_skill
            )
        
        # 3. 按优先级排序（P1优先，同层按priority数字，玩家优先于PC）
        # 格式：(技能, 归属方) 用于后续日志记录
        skills_to_execute = sorted(
            [(player_skill, "player"), (pc_skill, "pc")],
            key=lambda x: (
                x[0].priority_level.value,  # 先按层级（P1 < P2）
                x[0].priority,              # 再按优先级数字（越小越前）
                0 if x[1] == "player" else 1  # 最后按归属（玩家优先于PC）
            )
        )
        
        # 4. 依次执行技能效果（修改上下文）
        for skill, owner in skills_to_execute:
            self._execute_skill_effect(skill, owner, context)
        
        # 5. 最终伤害结算
        # 5a. 计算原始伤害 (逻辑来自原 damage_do)
        player_type = context.player_skill.type if context.player_skill else ""
        pc_type = context.pc_skill.type if context.pc_skill else ""
        
        player_countered = self.game.beats.get(player_type) == pc_type if player_type else False
        pc_countered = self.game.beats.get(pc_type) == player_type if pc_type else False
        
        # 玩家对PC的原始伤害
        pc_raw_damage = self._damage_calculate(
            context.player_skill.name, None, player_countered
        )
        # PC对玩家的原始伤害
        player_raw_damage = self._damage_calculate(
            context.pc_skill.name, None, pc_countered
        )
        
        # 5b. 应用伤害（调用带日志的 _apply_damage）
        # 玩家对PC的伤害：受击方是PC (target_is_player=False)
        context.pc_damage = self._damage_apply(
            target_is_player=False, 
            damage=pc_raw_damage,
            skill_name=context.player_skill.name
        )
        # PC对玩家的伤害：受击方是玩家 (target_is_player=True)
        context.player_damage = self._damage_apply(
            target_is_player=True, 
            damage=player_raw_damage,
            skill_name=context.pc_skill.name
        )
        # 6. 构建并返回结果
        return self._build_priority_result(context)
    
 