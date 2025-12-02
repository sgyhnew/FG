# 2.5

对combat进行完全解耦，多减少补，将其对其他类所有旧接口剔除，并优化战斗逻辑

## 1 combat

1.将CombatContext中大量冗余参数去除，只保留player_skill、pc_skill、player_input、combat_data。
2.优化combat_turn逻辑，将其中的阶段函数中的计算全部移植到combat_turn中，做到分工明确
3.修改原有的is判断函数，现保留is_alive和is_counter
4.将大量excute_和build_函数进行重构，只保留上下文结果构建函数_build_result和技能效果文本函数_build_effect
5.对damage_两个计算和应用的函数进行重构。符合MVC原则
6.对judge进行重构，将阶段函数phase_中的所有计算和判断移植到judge中，judge是combat中判断的唯一接口

## 2.main和attribute

1.对main和attribute中关于参入传入的数据类型进行规范，统一接口