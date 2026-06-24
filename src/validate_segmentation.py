import itk
import numpy as np

from src.segmentation import read_image


def compute_validation_metrics(
    mask_semi: np.ndarray, mask_auto: np.ndarray, voxel_volume: float
) -> tuple[float, float, float]:
    """
    Computes Dice coefficient, Jaccard Index (IoU), and absolute volume difference
    between two binary segmentation masks.
    """
    m_semi = (mask_semi > 0).astype(np.uint8)
    m_auto = (mask_auto > 0).astype(np.uint8)

    intersection = np.sum(np.logical_and(m_semi, m_auto))
    union = np.sum(np.logical_or(m_semi, m_auto))
    sum_semi = np.sum(m_semi)
    sum_auto = np.sum(m_auto)

    dice = (2.0 * intersection) / (sum_semi + sum_auto) if (sum_semi + sum_auto) > 0 else 0.0
    jaccard = intersection / union if union > 0 else 0.0

    vol_semi = sum_semi * voxel_volume
    vol_auto = sum_auto * voxel_volume
    vol_diff = abs(vol_semi - vol_auto)

    return dice, jaccard, vol_diff


def run_validation(label: str, mask_semi_path: str, mask_auto_path: str) -> None:
    """
    Reads the semi-automated and automated masks from files,
    computes validation metrics, and prints the result.
    """
    img_semi = read_image(mask_semi_path)
    img_auto = read_image(mask_auto_path)

    spacing = img_semi.GetSpacing()
    voxel_volume = spacing[0] * spacing[1] * spacing[2]

    arr_semi = itk.GetArrayFromImage(img_semi)
    arr_auto = itk.GetArrayFromImage(img_auto)

    dice, jaccard, vol_diff = compute_validation_metrics(arr_semi, arr_auto, voxel_volume)

    print(f"\nValidation metrics for {label}:")
    print(f"  Dice Coefficient:     {dice:.4f}")
    print(f"  Jaccard Index (IoU):  {jaccard:.4f}")
    print(f"  Absolute Volume Diff: {vol_diff:.2f} mm³")
