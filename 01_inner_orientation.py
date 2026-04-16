"""
01 内定向

作用：
把 Excel 中量测到的像素坐标 (i, j) 转换成像片坐标 (x, y)，单位 mm。

说明：
本项目是数字航空影像，没有传统四个框标点需要解仿射参数。
所以这里直接用固定相机参数：
    x = (i - 主点 i) * 像元大小
    y = (主点 j - j) * 像元大小
"""

from common import (
    CONTROL_XLSX,
    OBJECT_XLSX,
    OUTPUT_DIR,
    RELATIVE_XLSX,
    ensure_output_dir,
    pixel_to_photo,
    read_control_excel,
    read_object_excel,
    read_relative_excel,
    write_csv,
)


def add_photo_coordinates(points: list[dict]) -> list[dict]:
    """给每个点增加左右片像片坐标。"""
    result = []
    for p in points:
        left_x, left_y = pixel_to_photo(p["left_i"], p["left_j"])
        right_x, right_y = pixel_to_photo(p["right_i"], p["right_j"])

        q = dict(p)
        q["left_x"] = left_x
        q["left_y"] = left_y
        q["right_x"] = right_x
        q["right_y"] = right_y
        result.append(q)

    return result


def main() -> None:
    ensure_output_dir()

    relative_points = add_photo_coordinates(read_relative_excel())
    control_points = add_photo_coordinates(read_control_excel())
    object_points = add_photo_coordinates(read_object_excel())

    # 相对定向点输出
    write_csv(
        OUTPUT_DIR / "01_relative_photo_coords.csv",
        relative_points,
        ["id", "left_i", "left_j", "right_i", "right_j", "left_x", "left_y", "right_x", "right_y"],
    )

    # 像控点输出，保留地面坐标，后面绝对定向要用
    write_csv(
        OUTPUT_DIR / "01_control_photo_coords.csv",
        control_points,
        [
            "id",
            "number",
            "left_i",
            "left_j",
            "right_i",
            "right_j",
            "left_x",
            "left_y",
            "right_x",
            "right_y",
            "ground_x",
            "ground_y",
            "ground_z",
        ],
    )

    # 待成图地物点输出
    write_csv(
        OUTPUT_DIR / "01_object_photo_coords.csv",
        object_points,
        [
            "id",
            "object",
            "number",
            "left_i",
            "left_j",
            "right_i",
            "right_j",
            "left_x",
            "left_y",
            "right_x",
            "right_y",
        ],
    )

    print("内定向完成。")
    print(f"相对定向点来源：{RELATIVE_XLSX.name}，点数：{len(relative_points)}")
    print(f"像控点来源：{CONTROL_XLSX.name}，点数：{len(control_points)}")
    print(f"地物点来源：{OBJECT_XLSX.name}，点数：{len(object_points)}")
    print(f"结果已保存到：{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
