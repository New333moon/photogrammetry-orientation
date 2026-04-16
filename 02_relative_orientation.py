"""
02 相对定向

作用：
利用同名像点解左右片之间的 5 个相对定向元素。

未知数：
    phi1, kappa1, phi2, omega2, kappa2

基本思想：
同名点、左摄站、右摄站应该满足共面条件。
程序用高斯-牛顿迭代求解，雅可比矩阵用数值差分算，公式少一些，也更容易看懂。
"""

from pathlib import Path

import numpy as np

from common import FOCAL_LENGTH, OUTPUT_DIR, image_ray, read_csv, rotation_matrix


INPUT_CSV = OUTPUT_DIR / "01_relative_photo_coords.csv"
OUTPUT_PARAM = OUTPUT_DIR / "02_relative_parameters.txt"
OUTPUT_LOG = OUTPUT_DIR / "02_relative_iteration_log.csv"


def make_rotations(u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """由 5 个未知数生成左右片旋转矩阵。"""
    phi1, kappa1, phi2, omega2, kappa2 = u
    r_left = rotation_matrix(0.0, phi1, kappa1)
    r_right = rotation_matrix(omega2, phi2, kappa2)
    return r_left, r_right


def coplanarity_values(points: list[dict], u: np.ndarray) -> np.ndarray:
    """计算所有点的共面条件值。理论上这些值应接近 0。"""
    r_left, r_right = make_rotations(u)
    baseline = np.array([1.0, 0.0, 0.0], dtype=float)

    values = []
    for p in points:
        left_ray = image_ray(float(p["left_x"]), float(p["left_y"]), r_left)
        right_ray = image_ray(float(p["right_x"]), float(p["right_y"]), r_right)

        # 共面条件：B、left_ray、right_ray 三个向量的混合积为 0。
        value = np.dot(np.cross(baseline, left_ray), right_ray)
        values.append(value)

    return np.array(values, dtype=float)


def numerical_jacobian(points: list[dict], u: np.ndarray) -> np.ndarray:
    """用中心差分计算雅可比矩阵。"""
    step = 1e-6
    j = np.zeros((len(points), len(u)), dtype=float)

    for col in range(len(u)):
        du = np.zeros_like(u)
        du[col] = step
        f_plus = coplanarity_values(points, u + du)
        f_minus = coplanarity_values(points, u - du)
        j[:, col] = (f_plus - f_minus) / (2.0 * step)

    return j


def solve_relative_orientation(points: list[dict]) -> tuple[np.ndarray, list[dict]]:
    """迭代求解相对定向元素。"""
    u = np.zeros(5, dtype=float)
    log_rows = []

    for it in range(1, 51):
        f = coplanarity_values(points, u)
        j = numerical_jacobian(points, u)

        # 最小二乘求改正数：J * du = -f
        du, *_ = np.linalg.lstsq(j, -f, rcond=None)
        u = u + du

        rmse = float(np.sqrt(np.mean(f**2)))
        log_rows.append(
            {
                "iteration": it,
                "d_phi1": du[0],
                "d_kappa1": du[1],
                "d_phi2": du[2],
                "d_omega2": du[3],
                "d_kappa2": du[4],
                "condition_rmse": rmse,
            }
        )

        # 角元素改正数很小时停止。单位是弧度。
        if np.max(np.abs(du)) < 1e-10:
            break

    return u, log_rows


def write_iteration_log(path: Path, rows: list[dict]) -> None:
    """保存迭代过程。"""
    from common import write_csv

    write_csv(
        path,
        rows,
        ["iteration", "d_phi1", "d_kappa1", "d_phi2", "d_omega2", "d_kappa2", "condition_rmse"],
    )


def main() -> None:
    if not INPUT_CSV.exists():
        raise FileNotFoundError("请先运行 01_inner_orientation.py")

    points = read_csv(INPUT_CSV)
    u, log_rows = solve_relative_orientation(points)
    final_f = coplanarity_values(points, u)
    final_rmse = float(np.sqrt(np.mean(final_f**2)))

    write_iteration_log(OUTPUT_LOG, log_rows)

    names = ["phi1", "kappa1", "phi2", "omega2", "kappa2"]
    with OUTPUT_PARAM.open("w", encoding="utf-8") as f:
        f.write("# 相对定向元素，单位：弧度\n")
        f.write("# 基线长度在模型坐标中取 B = 1.0，后续绝对定向会统一缩放。\n")
        for name, value in zip(names, u):
            f.write(f"{name} = {value:.12f}\n")
        f.write(f"condition_rmse = {final_rmse:.12f}\n")
        f.write(f"focal_length_mm = {FOCAL_LENGTH:.6f}\n")

    print("相对定向完成。")
    for name, value in zip(names, u):
        print(f"{name} = {value:.12f} rad")
    print(f"共面条件 RMSE = {final_rmse:.6e}")
    print(f"参数保存到：{OUTPUT_PARAM}")
    print(f"迭代日志保存到：{OUTPUT_LOG}")


if __name__ == "__main__":
    main()
