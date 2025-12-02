from abc import ABC
from functools import lru_cache
from typing import Dict, Any, Callable, Tuple, Iterator
from dataclasses import dataclass
from FG.constants import PriorityLevel as PL
from func import load_json
@dataclass(frozen=True)
class SkillData(ABC):    # 通用技能属性
    name: str           # 技能名
    category: str       # 行动类别
    level: str          # 等级 

    cost: int = 0                            # 消耗
    cooldown: int =0                         # 冷却
    priority_level: PL = PL.P2               # 优先位阶
    priority: int=3                          # 优先级
    effect: str | Callable = '此招式没有效果' # 效果
    
    @classmethod
    def _base_data(cls, data: Dict[str,Any]) -> Dict[str,Any]:    # 可复用，公开的
        # 处理优先位阶转换
        priority_level_str = data.get('priority_level', 'P2')
        try:
            priority_level = PL[priority_level_str]
        except KeyError:
            priority_level = PL.P2
        return {    # 创建字典，传递时不传对象，方便cls继承
            'name': data['name'],
            'category': data['category'],
            'level': data['level'],
            'cost': data.get('cost', 0),
            'priority_level': priority_level,
            'priority': data.get('priority', 2),
            'effect': data.get('effect', ''),
            'cooldown': data.get('cooldown', 0)
        }
    @classmethod
    def from_dict(cls, data: Dict[str,Any]) -> 'SkillData':   # 父类的基础字典
        base_data = cls._base_data(data)    
        return cls(**base_data)  # 返回解包对象
@dataclass(frozen=True)
class AttackSkill(SkillData):   # 攻击技能
    damage: int = 0      # 伤害
    type:   str ='其他'  # 类型
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttackSkill':
        base_data = cls._base_data(data)
        return cls(
            **base_data,
            damage = data.get('damage',0),
            type = data.get('type','其他')
        )
@dataclass(frozen=True)
class DefenseSkill(SkillData):  # 防御技能
    defense_round: int = 1    # 生效回合数
    damage_reduction: int = 0 # 伤害减免
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DefenseSkill':
        base_data = cls._base_data(data)
        return cls(
            **base_data,
            defense_round = data.get('defense_round',1)
        )
    
class SkillManager:     # 技能管理器
    def __init__(self):
        self.skill = load_json('data/skill.json')
        self._skill_cache: Dict[str, SkillData] = {}
        self._build_skill()

    def _traverse_skill(self) -> Iterator[Tuple[str, str, str, Dict[str, Any]]]:   # 生成器迭代遍历
        """生成器：遍历技能树，产出(类别, 等级, 技能名, 数据字典)"""
        for category, levels in self.skill.items():
            for level, skills in levels.items():
                for name, data in skills.items():
                    yield category, level, name, data
    def _build_skill(self) -> None:                                                # 使用遍历结果构建技能缓存
        self._skill_cache.clear()
        SKILL_MAP = {
            'attack' : AttackSkill,
            'defense': DefenseSkill
        }
        for category, level, name, data in self._traverse_skill():
            skill_category = SKILL_MAP.get(category,SkillData)
            skills = {
                **data,
                'name'     : name,
                'category' : category,
                'level'    : level
            }
            self._skill_cache[name] = skill_category.from_dict(skills)

    @lru_cache(maxsize=64)  # 缓存查询结果，提升性能
    def get_skill(self, skill_name: str) -> SkillData:      # 查询技能元数据
        if skill_name not in self._skill_cache:
            raise KeyError(f"技能 '{skill_name}' 未定义，请检查 skill.json")
        return self._skill_cache[skill_name]
