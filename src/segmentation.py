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
