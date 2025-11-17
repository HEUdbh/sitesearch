import siteback.OneForAll.utils as utils

# 查看 utils 模块中实际可用的方法
print([method for method in dir(utils) if not method.startswith('_')])