"""
一键运行四个步骤。

也可以单独运行：
    python 01_inner_orientation.py
    python 02_relative_orientation.py
    python 03_forward_intersection.py
    python 04_absolute_orientation.py
"""

import subprocess
import sys


SCRIPTS = [
    "01_inner_orientation.py",
    "02_relative_orientation.py",
    "03_forward_intersection.py",
    "04_absolute_orientation.py",
]


def main() -> None:
    for script in SCRIPTS:
        print("\n" + "=" * 60)
        print(f"开始运行：{script}")
        print("=" * 60)
        subprocess.run([sys.executable, script], check=True)

    print("\n全部流程运行完成，结果在 outputs 文件夹。")


if __name__ == "__main__":
    main()
