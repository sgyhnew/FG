from enum import Enum,auto
import enum

class GameResult(Enum):     # 游戏结果名词
    ROUND = "round_start"          # 每回合开始
    COMBAT_WIN = "combat_victory"  # 胜利
    COMBAT_DRAW = "combat_draw"    # 平局
    DEFENSE_TURN = "defense_turn"  # 防御回合

class GamePhase(Enum):       # 游戏主阶段
    EXPLORATION =   "探索阶段"
    DIALOGUE =      "对话阶段"
    COMBAT =        "战斗阶段"  
    MENU =          "菜单界面"

# class FightEvent(Enum):      # 战斗特殊事件
    

class FightPhase(Enum):      # 战斗阶段
    PREPARE =        "准备阶段"    
    ACTION_PLAYER =  "玩家行动阶段"
    ACTION_PC =      "对手行动阶段"
    RESOLVE =        "结算阶段"

class GameMode(Enum):       # 游戏模式
    ADVENTURE  = '冒险模式'
    CHANLLENGE = '挑战模式' 

class MenuAction(Enum):     # 行动菜单
    ATTACK  = auto()
    SKILL   = auto()
    DEFENSE = auto()
    TOOL    = auto() 

class AttributeEvent(Enum): # 角色属性变化引发的事件
    FATAL = '受到致命伤'  # 受到致命伤害（重伤）
    CRITICAL = '重伤'    # 受到大量伤害
    HURT = '轻伤'      # 受到普通伤害
    DEATH = '阵亡'                 # 生命值归零
    MP_ADD = '能量增加'                       # 能量增加
    MP_SUB = '能量减少'                       # 能量减少

class SkillLevel(Enum):     # 技能等级
    LV1 = "lv1"
    LV2 = "lv2"
# class CharactersStatus(Enum):   # 角色buff和debuff

class PriorityLevel(Enum):  # 优先级
    P0 = 0  # 最高,不轻易启用
    P1 = 1  
    P2 = 2
    P3 = 3
    P4 = 4

BEATS_MAP = {               # 相克关系映射表
    "拳": "剑", 
    "剑": "刀", 
    "刀": "枪",
    "枪": "拳"
}

SAY_SPEED = 1.0  # 动画速度倍率