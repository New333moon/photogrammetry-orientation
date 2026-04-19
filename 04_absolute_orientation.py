"""
04 绝对定向
利用像控点进行7参数相似变换，通过迭代方法求解尺度、旋转和平移参数，再把模型坐标转换为地面坐标。
"""

import numpy as np
from tools import OUTPUT_DIR, read_csv, rotation_matrix, write_csv

# 输入
CONTROL_MODEL = OUTPUT_DIR / "03_control_model_points.csv"
OBJECT_MODEL = OUTPUT_DIR / "03_object_model_points.csv"

# 输出
PARAM_OUTPUT = OUTPUT_DIR / "04_absolute_parameters.txt"
CONTROL_RESIDUAL_OUTPUT = OUTPUT_DIR / "04_control_residuals.csv"
OBJECT_GROUND_OUTPUT = OUTPUT_DIR / "04_object_ground_points.csv"

def apply_similarity(points, tx, ty, tz, scale, omega, phi, kappa):
    rotation = rotation_matrix(omega, phi, kappa)
    transformed = scale * (rotation @ points.T).T
    transformed[:, 0] += tx
    transformed[:, 1] += ty
    transformed[:, 2] += tz
    return transformed


def numerical_jacobian(model_points, tx, ty, tz, scale, omega, phi, kappa):
    base = apply_similarity(model_points, tx, ty, tz, scale, omega, phi, kappa).reshape(-1)
    params = np.array([tx, ty, tz, scale, omega, phi, kappa], dtype=float)
    jacobian = np.zeros((base.size, 7))
    step = 1e-6

    for i in range(7):
        params_plus = params.copy()
        params_minus = params.copy()
        params_plus[i] += step
        params_minus[i] -= step

        plus = apply_similarity(
            model_points,
            params_plus[0],
            params_plus[1],
            params_plus[2],
            params_plus[3],
            params_plus[4],
            params_plus[5],
            params_plus[6],
        ).reshape(-1)
        minus = apply_similarity(
            model_points,
            params_minus[0],
            params_minus[1],
            params_minus[2],
            params_minus[3],
            params_minus[4],
            params_minus[5],
            params_minus[6],
        ).reshape(-1)

        jacobian[:, i] = (plus - minus) / (2 * step)

    return jacobian

# 用迭代方法求三维相似变换参数
def solve_similarity(model_points, ground_points):
    model_mean = model_points.mean(axis=0)
    ground_mean = ground_points.mean(axis=0)

    tx = ground_mean[0] - model_mean[0]
    ty = ground_mean[1] - model_mean[1]
    tz = ground_mean[2] - model_mean[2]

    model_dist = np.mean(np.linalg.norm(model_points - model_mean, axis=1))
    ground_dist = np.mean(np.linalg.norm(ground_points - ground_mean, axis=1))
    scale = ground_dist / model_dist if model_dist > 0 else 1.0

    omega = 0.0
    phi = 0.0
    kappa = 0.0

    for _ in range(50):
        fitted = apply_similarity(model_points, tx, ty, tz, scale, omega, phi, kappa)
        residual = (ground_points - fitted).reshape(-1)
        jacobian = numerical_jacobian(model_points, tx, ty, tz, scale, omega, phi, kappa)

        delta, *_ = np.linalg.lstsq(jacobian, residual, rcond=None)

        tx += delta[0]
        ty += delta[1]
        tz += delta[2]
        scale += delta[3]
        omega += delta[4]
        phi += delta[5]
        kappa += delta[6]

        limit_translation = np.max(np.abs(delta[:3]))
        limit_scale_angle = np.max(np.abs(delta[3:]))
        if limit_translation < 0.1 and limit_scale_angle < 1e-6:
            break

    rotation = rotation_matrix(omega, phi, kappa)
    translation = np.array([tx, ty, tz], dtype=float)
    return scale, rotation, translation

# 把模型点转换到地面坐标
def transform_points(points, scale, rotation, translation):
    transformed = scale * (rotation @ points.T).T
    return transformed + translation


def main():
    if not CONTROL_MODEL.exists() or not OBJECT_MODEL.exists():
        raise FileNotFoundError("请先运行 03_forward_intersection.py")

    control_rows = read_csv(CONTROL_MODEL)
    object_rows = read_csv(OBJECT_MODEL)

    # 整理像控点的模型坐标和地面坐标
    model_control = np.array(
        [[float(p["model_x"]), float(p["model_y"]), float(p["model_z"])] for p in control_rows]
    )
    ground_control = np.array(
        [[float(p["ground_x"]), float(p["ground_y"]), float(p["ground_z"])] for p in control_rows]
    )

    # 计算绝对定向参数
    scale, rotation, translation = solve_similarity(model_control, ground_control)

    # 像控点残差
    fitted_control = transform_points(model_control, scale, rotation, translation)
    residuals = fitted_control - ground_control
    rmse_xyz = np.sqrt(np.mean(residuals**2, axis=0))
    rmse_total = float(np.sqrt(np.mean(np.sum(residuals**2, axis=1))))

    residual_rows = []
    for row, fit, res in zip(control_rows, fitted_control, residuals):
        residual_rows.append(
            {
                "id": row["id"],
                "number": row["number"],
                "fit_x": fit[0],
                "fit_y": fit[1],
                "fit_z": fit[2],
                "vx": res[0],
                "vy": res[1],
                "vz": res[2],
            }
        )

    write_csv(
        CONTROL_RESIDUAL_OUTPUT,
        residual_rows,
        ["id", "number", "fit_x", "fit_y", "fit_z", "vx", "vy", "vz"],
    )

    # 把地物点从模型坐标转换到地面坐标
    model_object = np.array(
        [[float(p["model_x"]), float(p["model_y"]), float(p["model_z"])] for p in object_rows]
    )
    ground_object = transform_points(model_object, scale, rotation, translation)

    object_output_rows = []
    for row, ground in zip(object_rows, ground_object):
        object_output_rows.append(
            {
                "id": row["id"],
                "object": row["object"],
                "number": row["number"],
                "ground_x": ground[0],
                "ground_y": ground[1],
                "ground_z": ground[2],
                "Q": row["Q"],
                "ray_gap": row["ray_gap"],
            }
        )

    write_csv(
        OBJECT_GROUND_OUTPUT,
        object_output_rows,
        ["id", "object", "number", "ground_x", "ground_y", "ground_z", "Q", "ray_gap"],
    )

    with PARAM_OUTPUT.open("w", encoding="utf-8") as f:
        f.write("# 绝对定向参数:\n")
        f.write(f"lambda = {scale:.12f}\n")

        f.write(f"tx = {translation[0]:.12f}\n")
        f.write(f"ty = {translation[1]:.12f}\n")
        f.write(f"tz = {translation[2]:.12f}\n")
        
        f.write("旋转矩阵 =\n")
        for row in rotation:
            f.write("  " + " ".join(f"{v:.12f}" for v in row) + "\n")
        
        f.write(f"\nrmse_x = {rmse_xyz[0]:.6f}\n")
        f.write(f"rmse_y = {rmse_xyz[1]:.6f}\n")
        f.write(f"rmse_z = {rmse_xyz[2]:.6f}\n\n")
        f.write(f"rmse_total = {rmse_total:.6f}\n")

    print("绝对定向完成")
    print("控制点总 RMSE =", rmse_total)


if __name__ == "__main__":
    main()
