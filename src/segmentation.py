from typing import Any

import itk
import numpy as np


def read_image(filepath: str) -> Any:
    """
    Reads an ITK image from file.
    """
    return itk.imread(filepath)


def write_image(image: Any, filepath: str) -> None:
    """
    Writes an ITK image to file.
    """
    itk.imwrite(image, filepath)


def crop_image(
    image: Any, start: list[int] | tuple[int, ...], size: list[int] | tuple[int, ...]
) -> Any:
    """
    Crops an ITK image to a region of interest defined by start index and size.
    Both start and size should be 3-element lists/tuples in ITK coordinate order (x, y, z).
    """
    dimension = image.GetImageDimension()

    index_itk = itk.Index[dimension]()
    for i in range(dimension):
        index_itk[i] = int(start[i])

    size_itk = itk.Size[dimension]()
    for i in range(dimension):
        size_itk[i] = int(size[i])

    region = itk.ImageRegion[dimension]()
    region.SetIndex(index_itk)
    region.SetSize(size_itk)

    crop_filter = itk.RegionOfInterestImageFilter.New(Input=image, RegionOfInterest=region)
    crop_filter.Update()

    return crop_filter.GetOutput()


def confidence_connected_segmentation(
    image: Any,
    seed_points: list[list[int]],
    iterations: int = 5,
    multiplier: float = 2.5,
    neighborhood_radius: int = 1,
    replace_value: int = 1,
) -> Any:
    """
    Segment a region of interest using Confidence Connected Region Growing.
    """
    dimension = image.GetImageDimension()
    filter_cc = itk.ConfidenceConnectedImageFilter.New(Input=image)

    for seed in seed_points:
        idx = itk.Index[dimension]()
        for i in range(dimension):
            idx[i] = int(seed[i])
        filter_cc.AddSeed(idx)

    filter_cc.SetNumberOfIterations(iterations)
    filter_cc.SetMultiplier(multiplier)
    filter_cc.SetInitialNeighborhoodRadius(neighborhood_radius)
    filter_cc.SetReplaceValue(replace_value)

    filter_cc.Update()
    return filter_cc.GetOutput()


def connected_threshold_segmentation(
    image: Any,
    seed_points: list[list[int]],
    lower_threshold: float,
    upper_threshold: float,
    replace_value: int = 1,
) -> Any:
    """
    Segment a region of interest using Connected Threshold Region Growing.
    """
    dimension = image.GetImageDimension()
    filter_ct = itk.ConnectedThresholdImageFilter.New(Input=image)

    for seed in seed_points:
        idx = itk.Index[dimension]()
        for i in range(dimension):
            idx[i] = int(seed[i])
        filter_ct.AddSeed(idx)

    filter_ct.SetLower(lower_threshold)
    filter_ct.SetUpper(upper_threshold)
    filter_ct.SetReplaceValue(replace_value)

    filter_ct.Update()
    return filter_ct.GetOutput()


def morphological_opening(image: Any, radius: int = 1) -> Any:
    """
    Apply binary morphological opening to clean noise and smooth boundaries.
    """
    dimension = image.GetImageDimension()
    structuring_element = itk.FlatStructuringElement[dimension].Box(radius)

    filter_opening = itk.BinaryMorphologicalOpeningImageFilter.New(
        Input=image, Kernel=structuring_element
    )
    filter_opening.Update()
    return filter_opening.GetOutput()


def find_automatic_seed(image: Any, border_margin: int = 5) -> list[int]:
    """
    Finds a seed point automatically in the cropped image.
    Avoids the borders (defined by border_margin) to ignore skull/boundary hyper-intensities.
    Selects the voxel with the maximum intensity within the remaining inner region.
    Returns the coordinates in ITK index order [x, y, z].
    """
    arr = itk.GetArrayFromImage(image)

    # Take an inner sub-volume
    inner = arr[
        border_margin:-border_margin,
        border_margin:-border_margin,
        border_margin:-border_margin,
    ]

    # Find the maximum intensity index in the inner sub-volume
    max_idx_inner = np.unravel_index(np.argmax(inner), inner.shape)

    # Map back to full image numpy coordinates
    z = int(max_idx_inner[0] + border_margin)
    y = int(max_idx_inner[1] + border_margin)
    x = int(max_idx_inner[2] + border_margin)

    # Return as ITK coordinates [x, y, z]
    return [x, y, z]


def automated_segmentation(
    image: Any,
    iterations: int = 5,
    multiplier: float = 1.0,
    neighborhood_radius: int = 1,
    border_margin: int = 5,
) -> tuple[Any, list[int]]:
    """
    Performs fully automated segmentation on a cropped image by automatically
    finding a seed point (inner max intensity voxel) and growing the region.
    Returns the segmented mask and the seed point used.
    """
    seed = find_automatic_seed(image, border_margin=border_margin)
    mask = confidence_connected_segmentation(
        image,
        seed_points=[seed],
        iterations=iterations,
        multiplier=multiplier,
        neighborhood_radius=neighborhood_radius,
    )
    return mask, seed
