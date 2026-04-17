"""
02 相对定向
根据左右像片上的同名点，利用共面条件方程，迭代求解5个相对定向元素
"""

import numpy as np
from tools import OUTPUT_DIR, image_ray, read_csv, rotation_matrix, write_csv


INPUT_CSV = OUTPUT_DIR / "01_relative_photo_coords.csv"
OUTPUT_PARAM = OUTPUT_DIR / "02_relative_parameters.txt"
OUTPUT_LOG = OUTPUT_DIR / "02_relative_iteration_log.csv"

# 根据5个参数计算左右像片的旋转矩阵
def make_rotations(u):
    phi1, kappa1, phi2, omega2, kappa2 = u
    r_left = rotation_matrix(0.0, phi1, kappa1)
    r_right = rotation_matrix(omega2, phi2, kappa2)
    return r_left, r_right

# 计算每个点的共面条件值，正常情况下应该接近0
def coplanarity_values(points, u):
    r_left, r_right = make_rotations(u)
    baseline = np.array([1.0, 0.0, 0.0])

    values = []
    for p in points:
        left_ray = image_ray(float(p["left_x"]), float(p["left_y"]), r_left)
        right_ray = image_ray(float(p["right_x"]), float(p["right_y"]), r_right)

        # 如果三个向量共面，那么它们的混合积应当等于0
        value = np.dot(np.cross(baseline, left_ray), right_ray)
        values.append(value)

    return np.array(values)

# 用中心差分近似计算雅可比矩阵
def numerical_jacobian(points, u):
    step = 1e-6
    j = np.zeros((len(points), len(u)))

    for col in range(len(u)):
        du = np.zeros_like(u)
        du[col] = step
        f_plus = coplanarity_values(points, u + du)
        f_minus = coplanarity_values(points, u - du)
        j[:, col] = (f_plus - f_minus) / (2.0 * step)

    return j

# 通过迭代计算相对定向元素
def solve_relative_orientation(points):
    u = np.zeros(5)
    log_rows = []

    for it in range(1, 51):
        f = coplanarity_values(points, u)
        j = numerical_jacobian(points, u)

        # 用最小二乘方法求这一步的参数改正数
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

        if np.max(np.abs(du)) < 1e-10:
            break

    return u, log_rows

# 把每次迭代结果保存成CSV
def write_iteration_log(path, rows):
    write_csv(
        path,
        rows,
        ["iteration", "d_phi1", "d_kappa1", "d_phi2", "d_omega2", "d_kappa2", "condition_rmse"],
    )


def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError("请先运行 01_inner_orientation.py")

    # 读取内定向结果
    points = read_csv(INPUT_CSV)
    # 剔除了5个粗差较大的点
    points = [p for p in points if p["id"] not in {"x53", "x54", "x55", "x13","x42"}]
    # 计算相对定向参数
    u, log_rows = solve_relative_orientation(points)
    final_f = coplanarity_values(points, u)
    final_rmse = np.sqrt(np.mean(final_f**2))

    write_iteration_log(OUTPUT_LOG, log_rows)

    names = ["phi1", "kappa1", "phi2", "omega2", "kappa2"]
    with OUTPUT_PARAM.open("w", encoding="utf-8") as f:
        f.write("# 相对定向元素:\n")
        for name, value in zip(names, u):
            f.write(f"{name} = {value:.12f}\n")
        f.write(f"相对定向RMSE = {final_rmse:.12f}\n")

    print("相对定向完成")
    for name, value in zip(names, u):
        print(name, "=", value)
    print("RMSE =", final_rmse)
    print("参数文件已保存")
    for p, v in zip(points, final_f):
        print(p["id"], v)
    print("迭代日志已保存")


if __name__ == "__main__":
    main()
