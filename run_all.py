"""
按顺序运行四个摄影测量步骤：
1. 内定向
2. 相对定向
3. 前方交会
4. 绝对定向
"""

import subprocess #用来调用外部程序
import sys #用来获取当前Python解释器路径

def main():

    scripts = [
        "01_inner_orientation.py",
        "02_relative_orientation.py",
        "03_forward_intersection.py",
        "04_absolute_orientation.py"
    ]

    for script in scripts:
        print("\n" + "=" * 50)
        print(f"开始运行：{script}")
        print("=" * 50)
        subprocess.run([sys.executable, script])

    print("\n全部流程运行完成，结果在 outputs 文件夹。")


if __name__ == "__main__":
    main()
