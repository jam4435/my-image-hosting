import json
import os
import re
from pathlib import Path

# --- Configuration ---
BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / 'jm'
IMAGE_LIST_FILE = BASE_DIR / 'imageList.json'
INDEX_FILES = [BASE_DIR / 'imageIndex.json', IMAGE_DIR / 'imageIndex.json']
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.avif'}
KEYWORD_SPLIT_RE = re.compile(r'[-_·]+')
IGNORED_KEYWORDS = {'设定'}

# --- Helper Functions ---
def get_core_name(filename: str) -> str:
    """从完整文件名中提取核心部分（包含_后缀）。"""
    core, _ = os.path.splitext(filename)
    return core

def is_image_file(filename: str) -> bool:
    """判断文件名是否是图片文件。"""
    return Path(filename).suffix.lower() in IMAGE_EXTENSIONS

def is_valid_keyword(keyword: str) -> bool:
    """过滤无意义的索引词。"""
    if not keyword or keyword in IGNORED_KEYWORDS:
        return False
    if keyword.isdigit():
        return False
    if len(keyword) == 1 and keyword.isascii() and keyword.isalpha():
        return False
    return True

def extract_keywords_from_filename(filename: str) -> set[str]:
    """从单个文件名中提取所有“原子”关键词。"""
    base_name = get_core_name(filename)
    keywords = set()
    parts = KEYWORD_SPLIT_RE.split(base_name)
    keywords.update(part.strip() for part in parts if is_valid_keyword(part.strip()))
    return keywords

# --- Main Logic ---
def main():
    """主执行函数"""
    print("--- Image Index Builder (v6 - Image Only Keyword Rebuild) ---")

    with open(IMAGE_LIST_FILE, 'r', encoding='utf-8') as f:
        all_files = json.load(f)

    all_images = sorted(file for file in all_files if is_image_file(file))
    skipped_count = len(all_files) - len(all_images)
    print(f"[OK] Loaded {len(all_images)} image files from '{IMAGE_LIST_FILE}'.")
    if skipped_count:
        print(f"[INFO] Skipped {skipped_count} non-image files.")

    image_index = {}
    for image_file in all_images:
        keywords = extract_keywords_from_filename(image_file)
        for keyword in keywords:
            image_index.setdefault(keyword, []).append(image_file)

    # --- 4. 【最终版排序逻辑】---
    print("\nApplying final pinpoint sorting logic...")
    for keyword, file_list in image_index.items():
        file_list.sort(key=lambda filename: (
            # --- 主要规则: “后缀”长度 ---
            # 1. 获取文件名基础部分 (e.g., "敬国军·教官-特制皮鞭")
            # 2. 用当前关键词分割基础部分 (e.g., split by "教官")
            #    -> Result: ["敬国军·", "-特制皮鞭"]
            # 3. 取分割后的最后一部分，即“后缀” (e.g., "-特制皮鞭")
            # 4. 比较这个“后缀”的长度。长度越短，越核心，越靠前。
            len(get_core_name(filename).split(keyword)[-1]),
            
            # --- 次要规则: 核心度 (有无_) ---
            # 仅在上面“后缀”长度相同时生效。
            # 不带 '_' 的文件 (False=0) 排在带 '_' 的文件 (True=1) 之前。
            '_' in get_core_name(filename)
        ))
    print("[OK] All entries sorted.")

    # --- 5. 格式化并保存 ---
    sorted_index = {key: image_index[key] for key in sorted(image_index)}
    for index_file in dict.fromkeys(INDEX_FILES):
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_index, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Successfully saved index to '{index_file}'.")

if __name__ == "__main__":
    main()
