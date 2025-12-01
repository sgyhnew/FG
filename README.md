# 2.4.2版本更新

优化战斗系统的架构，将伤害的计算、应用，展示解耦

## 1 constants

增加新的AttributeEvent枚举类表示属性变化事件，目前只有血量

## 2 attribute

2.1新增类DamageResult明确damage_take返回的事件
2.2新增方法hp_get和hp_set，实现hp属性的规范调用，减少硬编码
2.3重构damage_take，移除所有硬编码和print输出，修改返回值为DamageResult，事件
中包含属性变化信息

## 3 combat

3.1新增方法_apply_damage，使其能调用attribute.damage_take作为战斗中应用伤害的唯一接口，返回事件并输出日志
3.2移除damage_do，将其重构
3.3重构judge，接管原damage_do中伤害计算控制逻辑，计算并应用
3.4重构_phase_resolve，将原本damage_take替换为_damage_apply
