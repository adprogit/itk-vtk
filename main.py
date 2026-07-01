"""
Mini Projet - module ITK/VTK
Auteurs : Klervi Choblet, Alex Dreau et Roman Miralves
"""

from src.recalage import recaler
from src.segmentation import (
    automated_segmentation,
    crop_image,
    morphological_opening,
    read_image,
    write_image,
)
from src.visualisation import visualize_simple


def main() -> None:
    gre1_path = "data/case6_gre1.nrrd"
    gre2_path = "data/case6_gre2.nrrd"
    roi_start = [60, 40, 40]
    roi_size = [60, 60, 30]

    print("Loading + cropping T1...")
    cropped_gre1 = crop_image(read_image(gre1_path), roi_start, roi_size)

    print("Recaling + cropping T2...")
    recaled = recaler(gre1_path, gre2_path)
    cropped_gre2 = crop_image(read_image(recaled), roi_start, roi_size)

    print("Connected threshold segmentation...")
    mask_auto_raw_gre1, _auto_seed_gre1 = automated_segmentation(
        cropped_gre1, lower_threshold=550, upper_threshold=1300, border_margin=5
    )
    mask_auto_raw_gre2, _auto_seed_gre2 = automated_segmentation(
        cropped_gre2, lower_threshold=550, upper_threshold=1300, border_margin=5
    )

    clean1 = morphological_opening(mask_auto_raw_gre1, radius=1)
    clean2 = morphological_opening(mask_auto_raw_gre2, radius=1)

    mask1_path = "data/mask_ct_gre1.nrrd"
    mask2_path = "data/mask_ct_gre2.nrrd"
    write_image(clean1, mask1_path)
    write_image(clean2, mask2_path)
    print(f"saved {mask1_path}, {mask2_path}")
    visualize_simple(gre1_path, recaled, mask1_path, mask2_path)


if __name__ == "__main__":
    main()
