### 运行说明

请在项目根目录下运行程序。输入数据已放在inputs文件夹中，程序运行后的结果会输出到outputs文件夹。

### 环境

本项目使用的依赖见pyproject.toml。

### 一次性运行

推荐直接运行总程序：
run_all.py
运行完成后，所有输出文件在outputs中。

### 分步运行

也可以按下面顺序逐个运行：
01_inner_orientation.py
02_relative_orientation.py
03_forward_intersection.py
04_absolute_orientation.py
后一步依赖前一步的输出，所以需要按顺序运行。

### 主要结果文件

需要检查的主要结果如下：
outputs/01_inner_parameters.txt 数字内定向元素
outputs/02_relative_parameters.txt 相对定向元素
outputs/04_absolute_parameters.txt 绝对定向元素

其他中间和检查结果：
outputs/01_relative_photo_coords.csv
outputs/01_control_photo_coords.csv
outputs/01_object_photo_coords.csv
outputs/02_relative_iteration_log.csv
outputs/03_control_model_points.csv
outputs/03_object_model_points.csv
outputs/04_control_residuals.csv
outputs/04_object_ground_points.csv
