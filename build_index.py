import json
import os
import re

# --- Configuration ---
# 定义输入和输出文件名，方便管理
IMAGE_LIST_FILE = 'image_list.json'
INDEX_FILE = 'imageIndex.json'

def extract_keywords_from_filename(filename: str) -> set[str]:
    """
    从单个文件名中提取所有可能的关键词。

    这是脚本的核心解析逻辑。
    例如: "南宫婉然-足部改造_设定.png" -> {"南宫婉然-足部改造", "南宫婉然", "足部改造"}
    """
    # 1. 移除文件扩展名 (e.g., .png, .webp)
    core_name, _ = os.path.splitext(filename)

    # 2. 移除类型后缀 (e.g., _设定, _详情)
    #    使用正则表达式，只分割第一次出现的 '_'
    core_name = re.split(r'_(?!.*_)', core_name)[0]
    
    keywords = set()
    
    # 3. 添加完整核心名作为关键词
    keywords.add(core_name)
    
    # 4. 用 '·' 和 '-' 分割，添加所有部分作为关键词
    #    将 '·' 统一替换为 '-'，然后按 '-' 分割
    parts = core_name.replace('·', '-').split('-')
    
    # 过滤掉空字符串并添加到集合中
    keywords.update(part for part in parts if part)
            
    return keywords

def main():
    """
    主执行函数
    """
    print("--- Image Index Builder ---")

    # --- 1. 加载数据 ---
    # 加载当前图片全量列表
    try:
        with open(IMAGE_LIST_FILE, 'r', encoding='utf-8') as f:
            all_images = json.load(f)
        print(f"✅ Successfully loaded {len(all_images)} images from '{IMAGE_LIST_FILE}'.")
    except FileNotFoundError:
        print(f"❌ Error: '{IMAGE_LIST_FILE}' not found. Please create it first.")
        return
    except json.JSONDecodeError:
        print(f"❌ Error: Could not parse '{IMAGE_LIST_FILE}'. Make sure it is a valid JSON list.")
        return

    # 加载现有的索引文件，如果不存在，则从空字典开始
    image_index = {}
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                image_index = json.load(f)
            print(f"✅ Successfully loaded existing index from '{INDEX_FILE}'.")
        except json.JSONDecodeError:
            print(f"⚠️ Warning: Could not parse existing '{INDEX_FILE}'. Starting with a new index.")
    else:
        print(f"ℹ️ Info: '{INDEX_FILE}' not found. A new index will be created.")

    # --- 2. 识别新图片 (非破坏性更新的核心) ---
    # 将现有索引中的所有图片名收集到一个集合中，用于快速查找
    processed_images = set()
    for images_in_list in image_index.values():
        processed_images.update(images_in_list)

    # 用集合运算找出 all_images 中未被处理过的新图片
    new_images = set(all_images) - processed_images

    if not new_images:
        print("\n✨ Index is already up-to-date. No new images found. Nothing to do.")
        return

    print(f"\n🔥 Found {len(new_images)} new images to process.")

    # --- 3. 处理新图片并智能合并 ---
    # 按字母顺序处理新图片，保证每次运行结果一致
    for image_file in sorted(list(new_images)):
        print(f"   -> Processing '{image_file}'...")
        keywords = extract_keywords_from_filename(image_file)
        
        for keyword in keywords:
            # 如果关键词是第一次出现，setdefault会创建一个空列表
            # 这一步保证了我们绝不会删除已有的键
            image_index.setdefault(keyword, [])
            
            # 只有当图片确实不在列表中时才添加
            # 这一步保证了我们绝不会重复添加，并保留您手动删除的操作
            if image_file not in image_index[keyword]:
                # **追加到列表末尾**，完美保留您手动调整过的顺序
                image_index[keyword].append(image_file)

    # --- 4. 格式化并保存 ---
    # 对顶级键（关键词）进行排序，让最终的JSON文件更易于阅读和手动查找
    sorted_index = {key: image_index[key] for key in sorted(image_index)}

    try:
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            # ensure_ascii=False 对于正确保存中文至关重要
            # indent=2 提供了优美的格式，方便手动编辑
            json.dump(sorted_index, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Successfully updated and saved index to '{INDEX_FILE}'.")
    except Exception as e:
        print(f"\n❌ Error: Failed to save the index file. Reason: {e}")


if __name__ == "__main__":
    main()