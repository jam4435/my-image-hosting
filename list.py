import os
import json

# --- 配置区 ---
# 请将这里的路径修改为你的图片所在的文件夹路径。
# 示例:

# folder_path = '/home/user/my-game/images'                 (Linux/Mac)
# 如果脚本就放在图片文件夹的上一级，也可以用相对路径:
# folder_path = 'images'
folder_path = 'C:/Users/DELL/my-image-hosting/jm'
# --- 配置区结束 ---

# 输出文件的名字
output_file = 'image_list.json'

print(f"正在扫描文件夹: '{folder_path}'...")

try:
    # 获取文件夹下所有条目（文件和子文件夹）的列表
    all_entries = os.listdir(folder_path)
    
    # 创建一个空列表，只用来存储文件名
    file_names = []
    
    # 遍历所有条目
    for entry_name in all_entries:
        # 构建完整的路径
        full_path = os.path.join(folder_path, entry_name)
        # 检查这个路径是否指向一个文件（而不是文件夹）
        if os.path.isfile(full_path):
            file_names.append(entry_name)
            
    # 将文件名列表写入JSON文件
    # 'w' 表示写入模式，会覆盖旧文件
    # encoding='utf-8' 确保中文等非英文字符能被正确处理
    with open(output_file, 'w', encoding='utf-8') as f:
        # json.dump 是将Python列表转换为JSON格式文本的核心函数
        # ensure_ascii=False 保证中文字符直接写入，而不是被转换成编码
        # indent=4 让输出的JSON文件格式化，更易于阅读
        json.dump(file_names, f, ensure_ascii=False, indent=4)
        
    print(f"✅ 成功！文件名列表已保存到 '{output_file}' 文件中。")
    print(f"共找到 {len(file_names)} 个文件。")

except FileNotFoundError:
    print(f"❌ 错误：找不到指定的文件夹路径 '{folder_path}'。")
    print("请检查 folder_path 变量是否设置正确。")
except Exception as e:
    print(f"❌ 发生了一个意外错误: {e}")