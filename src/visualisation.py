from typing import Any, TypeAlias

import itk
import numpy as np
import vtk
from vtkmodules.util.numpy_support import numpy_to_vtk

ITKImage: TypeAlias = Any
VTKImage: TypeAlias = Any


def load_image(path: str) -> ITKImage:
    """
    Loads an ITK image
    """
    return itk.imread(path, itk.F)


def itk_image_to_vtk_image(img: ITKImage) -> VTKImage:
    """
    Converts an ITK image into a VTK image
    """
    arr: np.ndarray = itk.array_from_image(img)
    arr = (arr > 0).astype(np.uint8)

    spacing: np.ndarray = img.GetSpacing()
    origin: np.ndarray = img.GetOrigin()

    new_img: VTKImage = vtk.vtkImageData()
    new_img.SetDimensions(arr.shape[2], arr.shape[1], arr.shape[0])
    new_img.SetSpacing(spacing[0], spacing[1], spacing[2])
    new_img.SetOrigin(origin[0], origin[1], origin[2])

    flat: np.ndarray = arr.flatten(order="C")
    vtk_arr: vtk.vtkDataArray = numpy_to_vtk(
        num_array=flat, deep=True, array_type=vtk.VTK_UNSIGNED_CHAR
    )  # type: ignore[no-untyped-call]

    new_img.GetPointData().SetScalars(vtk_arr)
    return new_img


def make_surface_actor(
    vtk_img: VTKImage, rgb: tuple[float, float, float], opacity: float
) -> vtk.vtkActor:
    """
    Creates an actor that highlights a surface with the given color
    """
    mc: vtk.vtkMarchingCubes = vtk.vtkMarchingCubes()
    mc.SetInputData(vtk_img)
    mc.SetValue(0, 0.5)
    mc.Update()

    smoother: vtk.vtkSmoothPolyDataFilter = vtk.vtkSmoothPolyDataFilter()
    smoother.SetInputConnection(mc.GetOutputPort())
    smoother.SetNumberOfIterations(30)
    smoother.SetRelaxationFactor(0.1)
    smoother.Update()

    normals: vtk.vtkPolyDataNormals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(smoother.GetOutputPort())
    normals.ConsistencyOn()
    normals.SplittingOff()

    mapper: vtk.vtkPolyDataMapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    mapper.ScalarVisibilityOff()

    actor: vtk.vtkActor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*rgb)
    actor.GetProperty().SetOpacity(opacity)
    actor.GetProperty().SetAmbient(0.2)
    actor.GetProperty().SetDiffuse(0.7)
    actor.GetProperty().SetSpecular(0.3)
    return actor


def main() -> None:
    segmentation1: ITKImage = load_image("../data/case6_gre1.nrrd")
    segmentation2: ITKImage = load_image("../data/case6_gre2.nrrd")
    # segmentation1: ITKImage = load_image("figures/segmentation_1.nrrd")
    # segmentation2: ITKImage = load_image("figures/segmentation_2.nrrd")

    vtk_seg1: VTKImage = itk_image_to_vtk_image(segmentation1)
    vtk_seg2: VTKImage = itk_image_to_vtk_image(segmentation2)

    pos_seg1: np.ndarray = (itk.array_from_image(segmentation1) > 0).astype(np.uint8)
    pos_seg2: np.ndarray = (itk.array_from_image(segmentation2) > 0).astype(np.uint8)

    spacing: Any = vtk_seg1.GetSpacing()
    volume_voxel: float = spacing[0] * spacing[1] * spacing[2]

    vol1: float = int(pos_seg1.sum()) * volume_voxel
    vol2: float = int(pos_seg2.sum()) * volume_voxel
    delta: float = vol2 - vol1
    delta_percent: float = (delta / vol1 * 100) if vol1 > 0 else 0.0

    inter: int = int(np.logical_and(pos_seg1, pos_seg2).sum())
    # union: int = int(np.logical_or(pos_seg1, pos_seg2).sum())

    sum1: float = pos_seg1.sum()
    sum2: float = pos_seg2.sum()
    dice: float = (2 * inter) / (sum1 + sum2) if (sum1 + sum2) > 0 else 0.0

    actor1: vtk.vtkActor = make_surface_actor(vtk_seg1, (1.0, 0.2, 0.2), 0.5)
    actor2: vtk.vtkActor = make_surface_actor(vtk_seg2, (0.2, 0.4, 1.0), 0.5)

    info: str = (
        f"Tumor evolution T1 → T2\n"
        f"Volume T1 : {vol1:.1f} mm³\n"
        f"Volume T2 : {vol2:.1f} mm³\n"
        f"Change    : {delta:+.1f} mm³  ({delta_percent:+.1f}%)\n"
        f"Dice      : {dice:.3f}"
    )

    text_actor: vtk.vtkTextActor = vtk.vtkTextActor()
    text_actor.SetInput(info)
    text_actor.GetTextProperty().SetFontSize(18)
    text_actor.GetTextProperty().SetColor(1.0, 1.0, 1.0)
    text_actor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
    text_actor.SetPosition(0.02, 0.02)

    sphere: vtk.vtkSphereSource = vtk.vtkSphereSource()
    sphere.Update()

    legend: vtk.vtkLegendBoxActor = vtk.vtkLegendBoxActor()
    legend.SetNumberOfEntries(2)
    legend.SetEntrySymbol(0, sphere.GetOutput())
    legend.SetEntryColor(0, 1.0, 0.2, 0.2)
    legend.SetEntryString(0, "T1 (baseline)")
    legend.SetEntrySymbol(1, sphere.GetOutput())
    legend.SetEntryColor(1, 0.2, 0.4, 1.0)
    legend.SetEntryString(1, "T2 (follow-up)")
    legend.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
    legend.SetPosition(0.75, 0.85)
    legend.SetPosition2(0.22, 0.12)

    renderer: vtk.vtkRenderer = vtk.vtkRenderer()
    renderer.AddActor(actor1)
    renderer.AddActor(actor2)
    renderer.AddViewProp(text_actor)
    renderer.AddViewProp(legend)
    renderer.SetBackground(0.1, 0.1, 0.15)
    renderer.ResetCamera()

    render_window: vtk.vtkRenderWindow = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetWindowName("Tumor Evolution — T1 vs T2")
    render_window.SetSize(1000, 800)

    interactor: vtk.vtkRenderWindowInteractor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)
    interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

    render_window.Render()
    interactor.Start()


if __name__ == "__main__":
    main()
