import json
import os
import re

# --- Configuration ---
IMAGE_LIST_FILE = 'imageList.json'
INDEX_FILE = 'imageIndex.json'

# --- Helper Functions ---
def get_core_name(filename: str) -> str:
    """从完整文件名中提取核心部分（包含_后缀）。"""
    core, _ = os.path.splitext(filename)
    return core

def get_base_name(filename: str) -> str:
    """从完整文件名中提取“基础”部分（不包含_后缀）。"""
    core_name = get_core_name(filename)
    base_name = re.split(r'_(?!.*_)', core_name)[0]
    return base_name

def extract_keywords_from_filename(filename: str) -> set[str]:
    """从单个文件名中提取所有“原子”关键词。"""
    base_name = get_base_name(filename)
    keywords = set()
    parts = base_name.replace('·', '-').split('-')
    keywords.update(part for part in parts if part)
    return keywords

# --- Main Logic ---
def main():
    """主执行函数"""
    print("--- Image Index Builder (v5 - Pinpoint Suffix Sorting) ---")

    # (省略了之前版本中重复的加载和错误处理代码，以聚焦核心)
    with open(IMAGE_LIST_FILE, 'r', encoding='utf-8') as f:
        all_images = json.load(f)
    print(f"✅ Loaded {len(all_images)} images.")

    image_index = {}
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            image_index = json.load(f)
        print(f"✅ Loaded existing index.")
    else:
        print(f"ℹ️ Creating a new index.")

    processed_images = set(img for imgs in image_index.values() for img in imgs)
    new_images = set(all_images) - processed_images

    if new_images:
        print(f"\n🔥 Found {len(new_images)} new images to process.")
        for image_file in sorted(list(new_images)):
            keywords = extract_keywords_from_filename(image_file)
            for keyword in keywords:
                image_index.setdefault(keyword, [])
                if image_file not in image_index[keyword]:
                    image_index[keyword].append(image_file)
    else:
        print("\n✨ Index is up-to-date.")

    # --- 4. 【最终版排序逻辑】---
    print("\n🔄 Applying final pinpoint sorting logic...")
    for keyword, file_list in image_index.items():
        file_list.sort(key=lambda filename: (
            # --- 主要规则: “后缀”长度 ---
            # 1. 获取文件名基础部分 (e.g., "敬国军·教官-特制皮鞭")
            # 2. 用当前关键词分割基础部分 (e.g., split by "教官")
            #    -> Result: ["敬国军·", "-特制皮鞭"]
            # 3. 取分割后的最后一部分，即“后缀” (e.g., "-特制皮鞭")
            # 4. 比较这个“后缀”的长度。长度越短，越核心，越靠前。
            len(get_base_name(filename).split(keyword)[-1]),
            
            # --- 次要规则: 核心度 (有无_) ---
            # 仅在上面“后缀”长度相同时生效。
            # 不带 '_' 的文件 (False=0) 排在带 '_' 的文件 (True=1) 之前。
            '_' in get_core_name(filename)
        ))
    print("✅ All entries sorted.")

    # --- 5. 格式化并保存 ---
    sorted_index = {key: image_index[key] for key in sorted(image_index)}
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(sorted_index, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Successfully saved index to '{INDEX_FILE}'.")

if __name__ == "__main__":
    main()