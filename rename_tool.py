import os
import sys

def process_single_file(filepath: str):
    """
    处理单个文件，将其文件名中的 '_' 替换为 '-'。
    """
    # 在 Windows 上，路径可能会被引号包裹，这里统一去掉
    clean_path = filepath.strip('"')

    if not os.path.isfile(clean_path):
        print(f"❌ [错误] 文件不存在或不是一个有效文件: {clean_path}")
        return

    directory, original_filename = os.path.split(clean_path)
    
    if '_' not in original_filename:
        print(f"⏭️ [跳过] 文件名中不含下划线: {original_filename}")
        return

    new_filename = original_filename.replace('_', '-')
    new_filepath = os.path.join(directory, new_filename)

    if os.path.exists(new_filepath):
        print(f"⚠️ [警告] 重命名失败，目标文件已存在: {new_filename}")
        return

    try:
        os.rename(clean_path, new_filepath)
        print(f"✅ [成功] '{original_filename}'  ->  '{new_filename}'")
    except Exception as e:
        print(f"❌ [错误] 重命名时发生意外错误: {e}")


def main():
    """
    主函数，处理通过命令行参数传入的文件。
    """
    # sys.argv[0] 是脚本自己的名字，所以我们从索引 1 开始读取文件路径
    filepaths = sys.argv[1:]

    print("--- 文件名下划线转连字符工具 ---")

    if not filepaths:
        print("\n用法错误：请不要直接运行此脚本。")
        print("正确用法是：将一个或多个文件直接拖拽到 'run_rename.bat' 文件上。")
        input("\n按 Enter 键退出。")
        return

    print(f"\n收到 {len(filepaths)} 个文件，开始处理...\n" + "-"*30)
    
    for path in filepaths:
        process_single_file(path)
    
    print("-"*30 + "\n处理完成。")


if __name__ == "__main__":
    main()