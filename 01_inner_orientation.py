"""
01 内定向
把左右片像素坐标转换为像片坐标，保存为CSV文件。
"""

from tools import (
    H0,H1,H2,K0,K1,K2, 
    OUTPUT_DIR,
    ensure_output_dir,pixel_to_photo,read_control_excel,read_object_excel,read_relative_excel,write_csv,
)

PARAM_OUTPUT = OUTPUT_DIR / "01_inner_parameters.txt"

# 给每个点增加左右片像片坐标
def add_photo_coordinates(points):
    result = []
    for p in points:
        left_x, left_y = pixel_to_photo(p["left_i"], p["left_j"])
        right_x, right_y = pixel_to_photo(p["right_i"], p["right_j"])

        point = dict(p)
        point["left_x"] = left_x
        point["left_y"] = left_y
        point["right_x"] = right_x
        point["right_y"] = right_y
        result.append(point)

    return result


def write_inner_parameters():
    with PARAM_OUTPUT.open("w", encoding="utf-8") as f:
        f.write("# 数字内定向元素:\n")
        f.write(f"h0 = {H0:.12f}\n")
        f.write(f"h1 = {H1:.12f}\n")
        f.write(f"h2 = {H2:.12f}\n\n")
        f.write(f"k0 = {K0:.12f}\n")
        f.write(f"k1 = {K1:.12f}\n")
        f.write(f"k2 = {K2:.12f}\n")


def main():
    ensure_output_dir()

    # 读取各类点并增加左右像片坐标
    relative_points = add_photo_coordinates(read_relative_excel())
    control_points = add_photo_coordinates(read_control_excel())
    object_points = add_photo_coordinates(read_object_excel())

    # 相对定向点输出
    write_csv(
        OUTPUT_DIR / "01_relative_photo_coords.csv",
        relative_points,
        ["id", "left_i", "left_j", "right_i", "right_j", "left_x", "left_y", "right_x", "right_y"],
    )

    # 像控点输出
    write_csv(
        OUTPUT_DIR / "01_control_photo_coords.csv",
        control_points,
        ["id", "number", "left_i", "left_j", "right_i", "right_j", "left_x", "left_y", "right_x", "right_y", "ground_x", "ground_y", "ground_z"],
    )

    # 地物点输出
    write_csv(
        OUTPUT_DIR / "01_object_photo_coords.csv",
        object_points,
        ["id","object","number","left_i","left_j","right_i","right_j","left_x","left_y","right_x","right_y"],
    )

    write_inner_parameters()

    print("内定向完成")
    print("数字内定向元素:", PARAM_OUTPUT)
    print("相对定向点数:", len(relative_points))
    print("像控点数:", len(control_points))
    print("地物点数:", len(object_points))


if __name__ == "__main__":
    main()
