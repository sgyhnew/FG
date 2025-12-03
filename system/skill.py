from abc import ABC
from functools import lru_cache
from typing import Dict, Any, Callable, Tuple, Iterator,List
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
        self.skill:Dict[str,Any] = load_json('data/skill.json')
        self.skill_manifest:Dict[str,List[str]] =load_json('data/skill_manifest.json')
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
    
    def _get_tokens(self, token: str) -> List[str]:  # 递归获取mainfest中所有技能名
        # case1：已经是最低层技能名
        if token in self._skill_cache:
            return [token]
       
        # case2：未定义，清单中不存在
        if token not in self.skill_manifest:
            raise KeyError(f"技能清单 '{token}' 未定义，请检查 skill_manifest.json")
       
        # case3: 清单中存在，递归展开
        out = []
        manifest_list = self.skill_manifest[token]

        # 校验清单，必须是列表
        if not isinstance(manifest_list, list):
            raise TypeError(f"技能清单 '{token}' 必须是列表，请检查 skill_manifest.json")
        
        for i in manifest_list:
            if not isinstance(i,str):
                raise TypeError(f"技能清单 '{token}' 中的元素必须是字符串，请检查 skill_manifest.json")
            out.extend(self._get_tokens(i))
        return out
    
    def get_skill_manifest(self, entity_id: str) -> List[SkillData]:
        """
        根据角色/实体ID获取其可用的技能数据结构，并完成 SkillData 对象的封装。
        """

        # 1. 检查角色/实体ID是否存在于清单中
        if entity_id not in self.skill_manifest:
            raise KeyError(f"角色技能清单ID '{entity_id}' 未找到。")
        
        # 2. 获取该ID在 skill_manifests中的原始数据
        manifest_data = self.skill_manifest[entity_id]

        # 3. 递归展开清单，获得扁平数据
        tokens: List[str] = []
        if isinstance(manifest_data,list):
            tokens = manifest_data
        elif isinstance(manifest_data,dict):
            for grp, id_list in manifest_data.items():
                if not isinstance(id_list,list):
                    raise TypeError(f"技能清单 '{entity_id}.{grp}'必须是List[str]")
                tokens.extend(id_list)
        else:
            raise TypeError(f"技能清单 '{entity_id}'必须是List[str]或Dict[str,List[str]]")

        # 4. 递归展开所有token -> 技能名
        skill_names: List[str] = []
        for token in tokens:
            skill_names.extend(self._get_tokens(token))

        # 5. 去重
        seen, unique = set(), []
        for name in skill_names:
            if name not in seen:
                unique.append(name)
                seen.add(name)

        # 6.转skilldata
        try:
            return [self.get_skill(n) for n in unique]
        except KeyError as e:
            raise KeyError(f"清单 '{entity_id}' 中的 {e.args[0]}") from e
