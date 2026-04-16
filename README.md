### 摄影测量四个定向程序

本项目按实习流程拆成四个程序：

1. `01_inner_orientation.py`：内定向，把像素坐标转为像片坐标。
2. `02_relative_orientation.py`：相对定向，解 5 个相对定向元素。
3. `03_forward_intersection.py`：前方交会，计算模型坐标。
4. `04_absolute_orientation.py`：绝对定向，把模型坐标转为地面坐标。

相机参数没有从 `inputs/camera` 读取，而是固定写在 `tools.py` 开头。

### 运行方法

推荐直接运行：

```bash
.venv/bin/python run_all.py
```

也可以按顺序单独运行：

```bash
.venv/bin/python 01_inner_orientation.py
.venv/bin/python 02_relative_orientation.py
.venv/bin/python 03_forward_intersection.py
.venv/bin/python 04_absolute_orientation.py
```

全部结果保存在 `outputs/` 文件夹，CSV 文件可以直接用 Excel 打开。

### 每一步输入输出对应关系

01 内定向
输入：inputs/\_.xlsx
输出：outputs/01\_\_\_photo_coords.csv
作用：i,j 像素坐标 → x,y 像片坐标

02 相对定向
输入：outputs/01_relative_photo_coords.csv
输出：outputs/02_relative_parameters.txt
作用：解左右片之间的 5 个相对定向元素

03 前方交会
输入：01 的像片坐标 + 02 的相对定向参数
输出：outputs/03\_\*\_model_points.csv
作用：左右光线交会 → 模型坐标

04 绝对定向
输入：outputs/03_control_model_points.csv 和 outputs/03_object_model_points.csv
输出：outputs/04_object_ground_points.csv
作用：模型坐标 → 地面坐标
