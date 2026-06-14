from typing import Any

import itk


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

