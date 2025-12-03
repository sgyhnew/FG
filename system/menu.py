
from __future__ import annotations

from ctypes.wintypes import SMALL_RECT
from typing import TYPE_CHECKING, Callable
if TYPE_CHECKING:
    from FG.main import Game
from func import say
from math import ceil
from dataclasses import dataclass
from typing import Dict, List, Tuple,Optional, Any

@dataclass
class MenuData:   # 菜单状态数据
    menu_type: str          # 菜单类型
    select_index: int = 0   # 选择索引
    page: int = 0           # 当前页码
    context: dict = None    # 上下文数据
    def __repr__(self):
        return f"MenuData(type={self.menu_type}, index={self.select_index}, page={self.page}, context={self.context})"
@dataclass
class MenuConfig: # 菜单配置
    title: str | Callable[[Dict], str]  # 标题或其生成函数
    build_options: Callable[['Menu',Dict], Dict[str,Tuple]] # 构建选项
    handle_choice: Callable[['Menu',str,Dict],Any]  # 处理选择
    show_cost: bool = True # 是否显示能量消耗词条

class MenuStack:  # 菜单栈，管理菜单状态
    def __init__(self, game):
        self.game = game
        self.stack : list[MenuData] = [MenuData('home')]  # 菜单栈初始化为空列表
        self.state_cache: Dict[str, MenuData] = {}  # 菜单状态缓存

    def push(self,menu_type: str, context: Dict = None) -> MenuData:   # 入栈

        if self.stack:  # 检测，获取当前栈
            current = self.stack[-1]
            self.state_cache[current.menu_type] = current
        
        # 创建或恢复新状态
        cache_key = f"{menu_type}_{context.get('category', '')}_{context.get('level', '')}" if context else menu_type
        new_state = self.state_cache.get(cache_key)
        if new_state:
            new_state.context = context
        else:
            new_state = MenuData(menu_type,0,0,context)
        
        
        self.stack.append(new_state)
        return new_state
    def pop(self) -> MenuData | None:      # 出栈
        if len(self.stack) > 1:
            popped = self.stack.pop()
            # 恢复上一菜单状态（从缓存）
            if self.stack:
                current = self.stack[-1]
                cached = self.state_cache.get(current.menu_type)
                if cached:
                    current.select_index = cached.select_index
                    current.page = cached.page
                    
            return popped
        return None  # 保持在栈底

    def get_current(self) -> MenuData | None:   # 获取当前菜单状态
        if self.stack:
            return self.stack[-1] 
        else: 
            print("当前菜单是空的")
            return None
    def clear(self):    # 清空栈并返回首页
        self.stack.clear()
        self.state_cache.clear()
        self.stack.append(MenuData('home'))
    def is_root(self) -> bool:           # 检查是否在根目菜单
        return len(self.stack) ==1

class Menu:       # 菜单系统，负责所有用户交互
    def __init__(self,game):
        self.game = game    # 外部调用
        self.attribute = game.attribute
        self.stack = MenuStack(game)  # 菜单栈
        self.menus = { # 菜单以及其配置
            'home':         self.menu_home(),      #主菜单
            # 'adventure':    self.menu_adventure(), #一级子菜单，冒险模式
            'chanllenge':   self.menu_chanllenge(),#一级子菜单，挑战模式(原main)
            'category':     self.menu_category(),  #二级子菜单，招式种类
            'level':        self.menu_level(),     #三级子菜单，招式等级
        }
    
    def navigate_to(            # 导航到指定菜单
            self, target_menu: str, context: Dict = None) -> bool:  
        try:
            # 确保状态栈有效
            if not self.stack.stack:
                self.stack.stack = [MenuData('home')]
            
            # 执行导航
            new_state = self.stack.push(target_menu, context)
            return True
        except Exception as e:
            print(f"[DEBUG] 导航失败: {e}")
            return False
    
    def go_back(self) -> bool:  # 返回上一级菜单
        return self.stack.pop() is not None
    
    def get_current_state(self) -> MenuData:    # 获取当前菜单状态
        return self.stack.get_current()
    
    def _update_state_selection(# 更新当前菜单状态的选择索引
            self, selected_key: str, options: Dict):  
        current_state = self.get_current_state()
        if current_state and selected_key in options:
            # 将选项键转换为索引（如 'a'->0, 'b'->1）
            keys = [k for k in options.keys() if k != 'z']  # 排除返回键
            if selected_key in keys:
                current_state.select_index = keys.index(selected_key)
    def _get_options_keys(      # 获取选项键列表，排除返回键 'z' 
            self, options: Dict) -> List[str]:   
        return [k for k in options.keys() if k != 'z']
    def _build_skill_menu(      # 构建技能菜单选项
            self, category: str, level: str) -> Dict[str, Tuple[str, bool, int]]: 
        options: Dict[str, Tuple[str, bool, int]] = {}
        key_index = ord('a')  # 初始值 = 97 98→'b'

        # 遍历技能缓存，筛选出对应类别的技能
        for skill_data in self.game.skill._skill_cache.values():
            
            if skill_data.category != category or skill_data.level != level:
                continue

            # 检查能量是否足够解锁该技能
            current_mp = self.game.attribute.mp_get(True)
            unlocked = current_mp >= skill_data.cost
            
            # 构建 options
            options[chr(key_index)] = (skill_data.name, unlocked, skill_data.cost)
            key_index += 1
        options['z'] = ('返回', True, 0)  # 返回选项
        return options
    def _get_available_levels(  # 获取指定类别的level
            self, category: str) -> List[str]:    
        levels = set()  # 集合
        for skill_data in self.game.skill._skill_cache.values():
            if skill_data.category == category:
                levels.add(skill_data.level)
        levels = sorted(levels) # 转化为有序列表
        return levels
    
    def debug_state(self):
        """调试状态信息"""
        print(f"\n=== 菜单状态调试 ===")
        print(f"栈深度: {len(self.stack.stack)}")
        for i, state in enumerate(self.stack.stack):
            print(f"  {i}: {state}")
        current = self.get_current_state()
        print(f"当前菜单: {current.menu_type if current else 'None'}")
        print(f"是否根菜单: {self.stack.is_root()}")
    
    def _render_menu(      # 分页，渲染菜单，复用
            self, options: Dict[str, Tuple[str, bool, int]],
            title: str,
            menu_type: str,
            page: int = 0,
            show_cost: bool = True
            ) -> str: 
        #options: {key: (name, unlocked, cost)}
        current_state = self.get_current_state()

        if page is None and current_state:
            page = current_state.page
        # 分页
        page_size = 4
        # 分离 'z' 返回键和其他选项
        chanllenge_items = [(k, v) for k, v in options.items() if k != 'z']
        # 总页数 = 总项数/4 ，向上取整
        total_pages = ceil(len(chanllenge_items) / page_size)

        if page is None:
            page =0
        
        while True:  # 分页循环
            # 更新当前状态页码
            if current_state:
                current_state.page = page
            # 显示标题
            print(f"\n{title}")
            
            # 计算当前页显示的选项
            start_idx = page * page_size
            end_idx = start_idx + page_size
            page_items = chanllenge_items[start_idx:end_idx]
            valid_keys = [k for k, _ in page_items]
            
            # 渲染当前页选项
            for key, (name, unlocked, cost) in page_items:
                # 构建基础status
                if show_cost:
                    status = f"(未解锁 需{cost}能量)" if not unlocked else f"(消耗{cost}能量)"
                else:
                    status = ''

                # 增强对技能的渲染
                if hasattr(self.game, 'get_skill'):
                    try:
                        skill_data = self.game.skill.get_skill(name)
                        # 显示伤害、冷却等信息
                        damage_info = f"伤害:{skill_data.damage}" if skill_data.damage > 0 else ""
                        cooldown_info = f"冷却:{skill_data.cooldown}" if skill_data.cooldown > 0 else ""
                        effect_info = f"效果:{skill_data.effect[:10]}..." if skill_data.effect else ""
                        
                        extra_info = " ".join(filter(None, [damage_info, cooldown_info, effect_info]))
                        if extra_info:
                            status = f"{status} [{extra_info}]"
                            
                    except KeyError:
                        pass  # 技能数据获取失败，使用基础显示
                
                print(f" [{key}] {name} {status}")
            
            # 底部控制栏
            controls = []
            if page > 0:
                controls.append(" [l] 上一页")
            if page < total_pages - 1:
                controls.append(" [r] 下一页")
            if menu_type != 'home':          
              controls.append(" [z] 返回")
            
            print("".join(controls))
            print(f" 第 {page + 1}/{total_pages} 页")
            
            # 获取用户输入
            choice = input(">>> ").strip().lower()
            
            # 处理翻页命令
            if choice == 'l' and page > 0:
                page -= 1
                continue
            if choice == 'r' and page < total_pages - 1:
                page += 1
                continue
            if choice == 'z':
                return '__back__'
            
            # 验证选择是否在当前页
            valid_keys = [k for k, _ in page_items] # 当前页有效键列表
            if choice in valid_keys:
                name, unlocked, cost = options[choice]
                if not unlocked:
                    say(f"对方摇了摇头：'阁下功力尚浅，尚未领悟此招（需{cost}能量）。'")
                    continue
                
                if self.game.attribute.mp_get(True) < cost:
                    say(f"能量不足{cost}点，无法施展此招！")
                    continue
                return choice  # 返回选项键
            
            # 无效输入
            say("该招式未习得，你思虑再三决定重新出招。")
            # 继续循环，保持在当前页
 
    def _run_menu(         # 通用菜单处理器
            self, menu_type: str, context: dict = None) -> Any:   
        current_state=self.get_current_state()  # 获取当前状态
        if current_state.menu_type != menu_type:
            raise NameError(f"菜单类型不匹配：期望 {menu_type}，实际 {current_state.menu_type}")
    
        config = self.menus[menu_type]
        # 构建选项
        options = config.build_options(self,context)    # 闭包函数build_options

        # 渲染并获得选择 (复原render)
        choice = self._render_menu(
            options,
            config.title(context) if callable(config.title) else config.title,
            menu_type,
            current_state.page,
            config.show_cost
            )
        
        # 处理选择
        result = config.handle_choice(self,choice,context)  # 闭包函数handle_choice

        return result

    def run(self) -> Any:  # 运行菜单系统 
        if not self.get_current_state():    # 防御检测，若无法得到当前状态返回home
            self.stack.clear()
            self.stack.push('home')     

        while 1:
            current_state = self.get_current_state()
            if not current_state:
                break
            # 统一调用_run处理器
            result = self._run_menu(current_state.menu_type,current_state.context)

            if result == '__navigate__': # 继续循环，自动获取新状态
                continue  
        
            if result == '__continue__': # 停留在当前菜单
                continue  
            
            if result == '__back__':     # 返回
                self.go_back()  
                continue
            if result == '__exit__':     # 退出
                return result

            if result is not None:
                return result
            
    # 菜单配置定义
    def menu_home(self) -> MenuConfig:
        def build_options(menu,ctx):
            return{
                'a':('冒险模式', True, 0),
                'b':('挑战模式', True, 0),
                'h':('帮助', True, 0),
                'q':('退出', True, 0),
            }
        def handle_choice(menu, choice, ctx):
            if choice == 'a':
                say("冒险模式正在开发中，敬请期待...")
                return '__continue__'
            elif choice == 'b':
                menu.navigate_to('chanllenge')
                return '__navigate__'
            elif choice == 'h':
                say("欢迎来到武侠世界！\n"
                    "- 挑战模式：与对手进行回合制战斗\n"
                    "- 使用不同等级的技能需要消耗能量\n"
                    "- 合理搭配攻击和防御策略才能获胜")
                return '__continue__'
            elif choice == 'q':
                say("青山不改，绿水长流，后会有期！")
                return '__exit__'
            return '__continue__'
        return MenuConfig(
            title="=== FG ===\n请选择游戏模式:",
            build_options=build_options,
            handle_choice=handle_choice,
            show_cost=False
        )

    def menu_chanllenge(self)-> MenuConfig:        # 挑战模式
        def build_options(menu,ctx):
            options = {
                'a': ('攻击', True, 0),
                'b': ('防御', True, 0),
                'h': ('帮助', True, 0),
                'q': ('逃跑', True, 0),
                'z': ('返回', True, 0)
            }                
            return options
        def handle_choice(menu,choice,ctx):
            if choice == 'a':
                menu.navigate_to('category',{'category':'attack'})
                return '__navigate__'   # 进入下级后立即返回，run处理
            if choice == 'b':
                menu.navigate_to('category', {'category': 'defense'})
                return '__navigate__'
            if choice == 'h':
                say("对方显然很有侠客精神，叮嘱你拳可剑、剑可刀、刀可枪、枪可拳，随着招式的熟练可以释放更具威力的招式。")
                return '__continue__'
            if choice == 'z' or choice == '__back__':
                say("对方仰天一笑，一个闪身便不知踪影。")
                return '__back__'
            if choice == 'q':
                say("你选择退出了游戏！")
                return '__exit__'
            return '__continue__'
        return MenuConfig(
            title='【回合开始】你略加思索，决定：',
            build_options = build_options,
            handle_choice = handle_choice,
            show_cost = False
        )
    def menu_category(self) -> MenuConfig:   # 行动类别菜单，一级子菜单
        def build_options(menu,ctx):
            category = ctx.get('category','')
            levels = menu._get_available_levels(category)
            options = {}
            for i,level in enumerate(levels):
                key = chr(ord('a')+i)
                count = sum(1 for s in menu.game.skill._skill_cache.values() if s.category == category and s.level == level)
                options[key] = (f"{level}级技能 ({count}种)", True, 0)
            options['z'] = ('返回',True,0)
            return options
        def handle_choice(menu,choice,ctx):
            if choice == '__back__' or choice == 'z': # 返回
                return '__back__'
            
            options = menu.menus['category'].build_options(menu, ctx)
            if choice in options:
                level_index = ord(choice) - ord('a')
                category = ctx.get('category', '')
                levels = menu._get_available_levels(category)
                if level_index < len(levels):
                    selected_level = levels[level_index]
                    menu.navigate_to('level', {
                        'category': category,
                        'level': selected_level
                    })
                    return '__navigate__'
            return '__continue__'
        return MenuConfig(
            title=lambda ctx: f"选择{ctx.get('category','')}技能等级",
            build_options = build_options,
            handle_choice = handle_choice,
            show_cost = False
        )
    def menu_level(self) -> MenuConfig:      # 等级菜单，二级子菜单
        def build_options(menu, ctx):
            return menu._build_skill_menu(
                ctx.get('category', ''), 
                ctx.get('level', '')
            )
        
        def handle_choice(menu, choice, ctx):
            if choice == '__back__' or choice == 'z':  # 返回
                return '__back__'
            
            options = menu.menus['level'].build_options(menu, ctx)
            if choice in options:
                skill_name, unlocked, cost = options[choice]
                
                # if not unlocked:
                #     say(f"技能'{skill_name}'尚未解锁...")
                #     return '__continue__'
                
                # if menu.attribute.mp_get(True) < cost:
                #     say(f"能量不足{cost}点...")
                #     return '__continue__'
                
                # 选择成功，清空栈并返回技能名
                menu.stack.clear()
                menu.stack.push('chanllenge')
                return skill_name
            
            return '__continue__'
        
        return MenuConfig(
            title=lambda ctx: f"选择{ctx.get('category', '')}技能 - {ctx.get('level', '')}",
            build_options=build_options,
            handle_choice=handle_choice,
            show_cost=True
        )

