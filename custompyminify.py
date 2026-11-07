# 极限压缩单个Python脚本文件的大小
import sys
import os
import argparse
import python_minifier

def minify_python_script(code_string):
    # 使用 python_minifier 进行极限压缩
    minified_codes = []
    for prefer_single_line in [True, False]:
        minified_code = python_minifier.minify(
            code_string,
            remove_annotations=python_minifier.RemoveAnnotationsOptions(
                remove_variable_annotations=True,
                remove_return_annotations=True,
                remove_argument_annotations=True,
                remove_class_attribute_annotations=True,
            ),
            remove_pass=True,
            remove_literal_statements=True,
            combine_imports=True,
            hoist_literals=True,
            rename_locals=True,
            preserve_locals=None,
            rename_globals=True,
            remove_object_base=True,
            convert_posargs_to_args=True,
            preserve_shebang=False,
            remove_asserts=True,
            remove_debug=True,
            remove_explicit_return_none=True,
            remove_builtin_exception_brackets=True,
            constant_folding=True,
            prefer_single_line=prefer_single_line,
        )
        minified_codes.append(minified_code)
    return sorted(minified_codes, key=len)[0]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Python Minifier Wrapper")
    parser.add_argument('-i', "--input_file", required=True)
    parser.add_argument('-o', "--output_file", required=True)
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        raise FileNotFoundError(f"输入文件不存在: {args.input_file}")
    elif not os.path.isfile(args.input_file):
        raise IsADirectoryError(f"输入路径不是文件: {args.input_file}")
    
    if os.path.exists(args.output_file):
        while True:
            overwrite = input(f"输出文件 {args.output_file} 已存在，是否覆盖？(y/n): ").strip().lower()
            if overwrite == 'y':
                break
            elif overwrite == 'n':
                print("操作已取消。")
                sys.exit(0)

    with open(args.input_file, "r", encoding="utf-8") as f:
        original_code = f.read()

    minified_code = minify_python_script(original_code)

    with open(args.output_file, "w", encoding="utf-8") as f:
        f.write(minified_code)

    original_size = len(original_code.encode("utf-8"))
    minified_size = len(minified_code.encode("utf-8"))
    reduction = original_size - minified_size
    reduction_percent = (reduction / original_size) * 100 if original_size > 0 else 0

    print(f"原始文件大小: {original_size} 字节")
    print(f"压缩后文件大小: {minified_size} 字节")
    print(f"减少了: {reduction} 字节 ({reduction_percent:.2f}%)")
