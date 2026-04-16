"""
03 前方交会

作用：
根据左右片像点和相对定向元素，计算模型坐标。

说明：
这里把模型空间中的基线 B 固定为 1。
因此得到的是“模型坐标”，尺度还不是实际地面尺度。
后面的绝对定向会利用像控点把它变到地面坐标系。
"""

import numpy as np

from photogrammetry_common import OUTPUT_DIR, image_ray, read_csv, rotation_matrix, write_csv


PARAM_FILE = OUTPUT_DIR / "02_relative_parameters.txt"
CONTROL_INPUT = OUTPUT_DIR / "01_control_photo_coords.csv"
OBJECT_INPUT = OUTPUT_DIR / "01_object_photo_coords.csv"
CONTROL_OUTPUT = OUTPUT_DIR / "03_control_model_points.csv"
OBJECT_OUTPUT = OUTPUT_DIR / "03_object_model_points.csv"


def read_relative_parameters() -> np.ndarray:
    """读取相对定向结果。"""
    if not PARAM_FILE.exists():
        raise FileNotFoundError("请先运行 02_relative_orientation.py")

    values = {}
    for line in PARAM_FILE.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.strip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = float(value.strip())

    return np.array(
        [values["phi1"], values["kappa1"], values["phi2"], values["omega2"], values["kappa2"]],
        dtype=float,
    )


def make_rotations(u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """生成左右片旋转矩阵。"""
    phi1, kappa1, phi2, omega2, kappa2 = u
    r_left = rotation_matrix(0.0, phi1, kappa1)
    r_right = rotation_matrix(omega2, phi2, kappa2)
    return r_left, r_right


def intersect_one_point(p: dict, r_left: np.ndarray, r_right: np.ndarray) -> dict:
    """计算一个同名点的模型坐标。"""
    baseline = 1.0

    left_ray = image_ray(float(p["left_x"]), float(p["left_y"]), r_left)
    right_ray = image_ray(float(p["right_x"]), float(p["right_y"]), r_right)

    # 由 x、z 两个方向求左右光线上的比例系数。
    den = left_ray[0] * right_ray[2] - right_ray[0] * left_ray[2]
    if abs(den) < 1e-12:
        raise ValueError(f"点 {p['id']} 的交会几何太差，分母接近 0")

    n1 = baseline * right_ray[2] / den
    n2 = baseline * left_ray[2] / den

    # 左右光线分别算出的点。由于有误差，两点一般不会完全重合。
    p_left = n1 * left_ray
    p_right = np.array([baseline, 0.0, 0.0], dtype=float) + n2 * right_ray

    # 取两条光线最近位置的中点作为模型点。
    model = (p_left + p_right) / 2.0
    gap = p_left - p_right

    result = dict(p)
    result["model_x"] = model[0]
    result["model_y"] = model[1]
    result["model_z"] = model[2]
    result["y_parallax"] = gap[1]
    result["ray_gap"] = float(np.linalg.norm(gap))
    return result


def forward_points(points: list[dict], u: np.ndarray) -> list[dict]:
    """批量前方交会。"""
    r_left, r_right = make_rotations(u)
    return [intersect_one_point(p, r_left, r_right) for p in points]


def main() -> None:
    if not CONTROL_INPUT.exists() or not OBJECT_INPUT.exists():
        raise FileNotFoundError("请先运行 01_inner_orientation.py")

    u = read_relative_parameters()
    control_model = forward_points(read_csv(CONTROL_INPUT), u)
    object_model = forward_points(read_csv(OBJECT_INPUT), u)

    control_fields = [
        "id",
        "number",
        "model_x",
        "model_y",
        "model_z",
        "y_parallax",
        "ray_gap",
        "ground_x",
        "ground_y",
        "ground_z",
    ]
    object_fields = ["id", "object", "number", "model_x", "model_y", "model_z", "y_parallax", "ray_gap"]

    write_csv(CONTROL_OUTPUT, control_model, control_fields)
    write_csv(OBJECT_OUTPUT, object_model, object_fields)

    control_gap = np.array([float(p["ray_gap"]) for p in control_model])
    object_gap = np.array([float(p["ray_gap"]) for p in object_model])

    print("前方交会完成。")
    print(f"像控点模型坐标：{CONTROL_OUTPUT}")
    print(f"地物点模型坐标：{OBJECT_OUTPUT}")
    print(f"像控点光线间距平均值：{control_gap.mean():.6e}")
    print(f"地物点光线间距平均值：{object_gap.mean():.6e}")


if __name__ == "__main__":
    main()
