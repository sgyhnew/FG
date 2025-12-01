# 2.4.3版本更新

对combat的结构进行优化

## 1 combat

1.将原有的多个上下文类合并，现在只保留两个：CombatContext和CombatData
2.修改combat中大量方法关于旧PhaseData的接口
3.移除了defense_skill这个多余属性，归类为player_skill和pc_skill中，并增肌新的防御状态判断is_defense_turn
