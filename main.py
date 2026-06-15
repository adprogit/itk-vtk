import itk
import numpy as np
from src.segmentation import (
    automated_segmentation,
    confidence_connected_segmentation,
    crop_image,
    morphological_opening,
    read_image,
    write_image,
)


def main() -> None:
    # Paths
    gre1_path = "data/case6_gre1.nrrd"
    gre2_path = "data/case6_gre2.nrrd"

    # Bounding Box (ROI) in ITK coordinates
    roi_start = [60, 40, 40]
    roi_size = [60, 60, 30]

    print("Loading original volumes...")
    image_gre1 = read_image(gre1_path)
    image_gre2 = read_image(gre2_path)

    print("Cropping volumes to ROI...")
    cropped_gre1 = crop_image(image_gre1, roi_start, roi_size)
    cropped_gre2 = crop_image(image_gre2, roi_start, roi_size)

    # --- Semi-Automated Segmentation ---
    # Manual seed points inside the bright active tumor region
    # gre1: [20, 7, 13], gre2: [24, 18, 13]
    seed_gre1 = [[20, 7, 13]]
    seed_gre2 = [[24, 18, 13]]

    print("\nRunning Confidence Connected Segmentation (Semi-Automated)...")
    mask_cc_gre1 = confidence_connected_segmentation(
        cropped_gre1, seed_gre1, iterations=5, multiplier=1.0, neighborhood_radius=1
    )
    mask_cc_gre2 = confidence_connected_segmentation(
        cropped_gre2, seed_gre2, iterations=5, multiplier=1.0, neighborhood_radius=1
    )

    print("Applying morphological opening to clean semi-auto masks...")
    clean_mask_gre1 = morphological_opening(mask_cc_gre1, radius=1)
    clean_mask_gre2 = morphological_opening(mask_cc_gre2, radius=1)

    # Save semi-automated masks
    mask_gre1_path = "data/mask_semi_gre1.nrrd"
    mask_gre2_path = "data/mask_semi_gre2.nrrd"
    write_image(clean_mask_gre1, mask_gre1_path)
    write_image(clean_mask_gre2, mask_gre2_path)
    print(f"Saved T1 semi-auto mask to {mask_gre1_path}")
    print(f"Saved T2 semi-auto mask to {mask_gre2_path}")

    # --- Automated Segmentation ---
    print("\nRunning Automated Segmentation...")
    # Fully automated segmentation using automatic seed selection (inner max intensity)
    mask_auto_raw_gre1, auto_seed_gre1 = automated_segmentation(
        cropped_gre1, iterations=5, multiplier=1.0, neighborhood_radius=1, border_margin=5
    )
    mask_auto_raw_gre2, auto_seed_gre2 = automated_segmentation(
        cropped_gre2, iterations=5, multiplier=1.0, neighborhood_radius=1, border_margin=5
    )

    print("Applying morphological opening to clean auto masks...")
    clean_auto_mask_gre1 = morphological_opening(mask_auto_raw_gre1, radius=1)
    clean_auto_mask_gre2 = morphological_opening(mask_auto_raw_gre2, radius=1)

    # Save automated masks
    mask_auto_gre1_path = "data/mask_auto_gre1.nrrd"
    mask_auto_gre2_path = "data/mask_auto_gre2.nrrd"
    write_image(clean_auto_mask_gre1, mask_auto_gre1_path)
    write_image(clean_auto_mask_gre2, mask_auto_gre2_path)
    print(f"Saved T1 automated mask to {mask_auto_gre1_path}")
    print(f"Saved T2 automated mask to {mask_auto_gre2_path}")

    # --- Quantitative Comparison ---
    print("\n=======================================================")
    print("QUANTITATIVE COMPARISON OF SEGMENTATION RESULTS")
    print("=======================================================")

    for label, mask_semi, mask_auto, auto_seed, man_seed in [
        ("T1 (Baseline)", clean_mask_gre1, clean_auto_mask_gre1, auto_seed_gre1, seed_gre1[0]),
        ("T2 (Follow-up)", clean_mask_gre2, clean_auto_mask_gre2, auto_seed_gre2, seed_gre2[0]),
    ]:
        spacing = mask_semi.GetSpacing()
        voxel_volume = spacing[0] * spacing[1] * spacing[2]

        arr_semi = itk.GetArrayFromImage(mask_semi)
        arr_auto = itk.GetArrayFromImage(mask_auto)

        voxels_semi = np.sum(arr_semi > 0)
        voxels_auto = np.sum(arr_auto > 0)

        vol_semi = voxels_semi * voxel_volume
        vol_auto = voxels_auto * voxel_volume

        print(f"\n{label}:")
        print(f"  Semi-Automated Seed: {man_seed}")
        print(f"  Automated Seed:      {auto_seed}")
        print(f"  Semi-Automated Voxel Count: {voxels_semi:5d} | Volume: {vol_semi:8.2f} mm³")
        print(f"  Automated Voxel Count:      {voxels_auto:5d} | Volume: {vol_auto:8.2f} mm³")


if __name__ == "__main__":
    main()
