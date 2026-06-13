from src.segmentation import read_image, write_image, crop_image

def main():
    gre1_path = "data/case6_gre1.nrrd"
    gre2_path = "data/case6_gre2.nrrd"

    roi_start = [60, 40, 40]
    roi_size = [60, 60, 30]

    print("Loading original volumes...")
    image_gre1 = read_image(gre1_path)
    image_gre2 = read_image(gre2_path)

    print(f"Cropping gre1 with ROI Start={roi_start}, Size={roi_size}...")
    cropped_gre1 = crop_image(image_gre1, roi_start, roi_size)
    cropped_gre1_path = "data/cropped_case6_gre1.nrrd"
    write_image(cropped_gre1, cropped_gre1_path)
    print(f"Saved cropped gre1 to {cropped_gre1_path}")

    print(f"Cropping gre2 with ROI Start={roi_start}, Size={roi_size}...")
    cropped_gre2 = crop_image(image_gre2, roi_start, roi_size)
    cropped_gre2_path = "data/cropped_case6_gre2.nrrd"
    write_image(cropped_gre2, cropped_gre2_path)
    print(f"Saved cropped gre2 to {cropped_gre2_path}")

    print("\nVerification of cropped volumes:")
    for f in [cropped_gre1_path, cropped_gre2_path]:
        img = read_image(f)
        size = img.GetLargestPossibleRegion().GetSize()
        spacing = img.GetSpacing()
        print(f"  {f} -> Size: {list(size)}, Spacing: {list(spacing)}")

if __name__ == "__main__":
    main()
