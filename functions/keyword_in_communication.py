# -*- coding: utf-8 -*-
keys = dict()
keys['playername'] = '一段关于这个玩家的介绍，用于提供给AI的上下文提示词'
new_keys = {k.lower():v for k,v in keys.items()} # 小写索引
keys.update(new_keys) # 更新原来的字典
keys_set = set(keys) # 搜索索引，一个集合
