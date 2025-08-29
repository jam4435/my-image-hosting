import json
import os
import re

# --- Configuration ---
IMAGE_LIST_FILE = 'image_list.json'
INDEX_FILE = 'imageIndex.json'

def extract_keywords_from_filename(filename: str) -> set[str]:
    """
    从单个文件名中提取所有可能的关键词。
    
    修正版逻辑: 只提取通过分隔符拆分后的“原子”关键词。
    例如: "南宫婉然-足部改造_设定.png" -> {"南宫婉然", "足部改造"}
    不再包含 "南宫婉然-足部改造" 这种组合名。
    """
    # 1. 移除文件扩展名
    core_name, _ = os.path.splitext(filename)

    # 2. 移除类型后缀
    core_name = re.split(r'_(?!.*_)', core_name)[0]
    
    keywords = set()
    
    # 3. 【核心修改】我们不再需要添加完整的核心名作为关键词
    #    之前这行代码是: keywords.add(core_name)
    #    我们直接将其移除，只保留下面的拆分逻辑。
    
    # 4. 用 '·' 和 '-' 分割，添加所有部分作为关键词
    parts = core_name.replace('·', '-').split('-')
    
    # 只将拆分后的部分作为最终的关键词
    keywords.update(part for part in parts if part)
            
    return keywords

def main():
    """
    主执行函数
    """
    print("--- Image Index Builder ---")

    # --- 1. 加载数据 ---
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

    # --- 2. 识别新图片 ---
    processed_images = set()
    for images_in_list in image_index.values():
        processed_images.update(images_in_list)

    new_images = set(all_images) - processed_images

    if not new_images:
        print("\n✨ Index is already up-to-date. No new images found. Nothing to do.")
        return

    print(f"\n🔥 Found {len(new_images)} new images to process.")

    # --- 3. 处理新图片并智能合并 ---
    for image_file in sorted(list(new_images)):
        print(f"   -> Processing '{image_file}'...")
        keywords = extract_keywords_from_filename(image_file)
        
        for keyword in keywords:
            image_index.setdefault(keyword, [])
            if image_file not in image_index[keyword]:
                image_index[keyword].append(image_file)

    # --- 4. 格式化并保存 ---
    sorted_index = {key: image_index[key] for key in sorted(image_index)}

    try:
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorted_index, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Successfully updated and saved index to '{INDEX_FILE}'.")
    except Exception as e:
        print(f"\n❌ Error: Failed to save the index file. Reason: {e}")


if __name__ == "__main__":
    main()