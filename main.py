import itk
import numpy as np
from src.segmentation import (
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

    # Seed points inside the bright active tumor region
    # gre1: [20, 7, 13]
    # gre2: [24, 18, 13]
    seed_gre1 = [[20, 7, 13]]
    seed_gre2 = [[24, 18, 13]]

    print("\nRunning Confidence Connected Segmentation (Multiplier=1.0)...")
    # Multiplier=1.0 prevents the region growing from leaking into healthy brain tissue
    mask_cc_gre1 = confidence_connected_segmentation(
        cropped_gre1, seed_gre1, iterations=5, multiplier=1.0, neighborhood_radius=1
    )
    mask_cc_gre2 = confidence_connected_segmentation(
        cropped_gre2, seed_gre2, iterations=5, multiplier=1.0, neighborhood_radius=1
    )

    print("Applying morphological opening to clean masks...")
    clean_mask_gre1 = morphological_opening(mask_cc_gre1, radius=1)
    clean_mask_gre2 = morphological_opening(mask_cc_gre2, radius=1)

    # Save the resulting segmentation masks
    mask_gre1_path = "data/mask_semi_gre1.nrrd"
    mask_gre2_path = "data/mask_semi_gre2.nrrd"
    write_image(clean_mask_gre1, mask_gre1_path)
    write_image(clean_mask_gre2, mask_gre2_path)
    print(f"Saved T1 semi-auto mask to {mask_gre1_path}")
    print(f"Saved T2 semi-auto mask to {mask_gre2_path}")

    # Quantitative analysis of the tumor
    print("\nQuantitative analysis of semi-automated segmentation:")
    for name, mask_path in [
        ("T1 (Baseline)", mask_gre1_path),
        ("T2 (Follow-up)", mask_gre2_path),
    ]:
        mask_img = read_image(mask_path)
        spacing = mask_img.GetSpacing()
        voxel_volume = spacing[0] * spacing[1] * spacing[2]

        mask_arr = itk.GetArrayFromImage(mask_img)
        tumor_voxel_count = np.sum(mask_arr > 0)
        tumor_volume = tumor_voxel_count * voxel_volume

        print(f"  {name}:")
        print(f"    Tumor voxel count: {tumor_voxel_count}")
        print(f"    Tumor volume: {tumor_volume:.2f} mm³")


if __name__ == "__main__":
    main()
