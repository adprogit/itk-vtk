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

    new_img: VTKImage = vtk.vtkImageData()
    new_img.SetDimensions(arr.shape[2], arr.shape[1], arr.shape[0])
    new_img.SetSpacing(1.0, 1.0, 1.0)
    new_img.SetOrigin(0.0, 0.0, 0.0)

    flat: np.ndarray = arr.flatten(order="C")
    vtk_arr: vtk.vtkDataArray = numpy_to_vtk(
        num_array=flat, deep=True, array_type=vtk.VTK_UNSIGNED_CHAR
    )  # type: ignore[no-untyped-call]

    new_img.GetPointData().SetScalars(vtk_arr)
    return new_img


def itk_ct_to_vtk_ct(img: ITKImage) -> VTKImage:
    """
    Converts an ITK ct into a VTK ct
    """
    arr: np.ndarray = itk.array_from_image(img).astype(np.float32)

    vtk_img: VTKImage = vtk.vtkImageData()
    vtk_img.SetDimensions(arr.shape[2], arr.shape[1], arr.shape[0])
    vtk_img.SetSpacing(1.0, 1.0, 1.0)
    vtk_img.SetOrigin(0.0, 0.0, 0.0)

    vtk_arr: vtk.vtkDataArray = numpy_to_vtk(
        num_array=arr.flatten(order="C"),
        deep=True,
        array_type=vtk.VTK_FLOAT,
    )  # type: ignore[no-untyped-call]

    vtk_img.GetPointData().SetScalars(vtk_arr)
    return vtk_img


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
    normals.AutoOrientNormalsOn()
    normals.SplittingOff()

    mapper: vtk.vtkPolyDataMapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    mapper.ScalarVisibilityOff()

    actor: vtk.vtkActor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*rgb)
    actor.GetProperty().SetAmbientColor(*rgb)
    actor.GetProperty().SetSpecularColor(1.0, 1.0, 1.0)
    actor.GetProperty().SetOpacity(opacity)
    actor.GetProperty().SetAmbient(1.0)
    actor.GetProperty().SetDiffuse(0.2)
    actor.GetProperty().SetSpecular(0.8)
    actor.GetProperty().SetSpecularPower(50)

    return actor


def make_volume_actor(vtk_img: VTKImage) -> vtk.vtkVolume:
    """
    Creates an actor that represents the skull of the patient
    """
    lo, hi = vtk_img.GetScalarRange()
    mid: float = lo + (hi - lo) * 0.4

    color_tf: vtk.vtkColorTransferFunction = vtk.vtkColorTransferFunction()
    color_tf.AddRGBPoint(lo, 0.0, 0.0, 0.0)
    color_tf.AddRGBPoint(hi, 1.0, 1.0, 1.0)

    opacity_tf: vtk.vtkPiecewiseFunction = vtk.vtkPiecewiseFunction()
    opacity_tf.AddPoint(lo, 0.00)
    opacity_tf.AddPoint(mid, 0.02)
    opacity_tf.AddPoint(hi, 0.08)

    prop: vtk.vtkVolumeProperty = vtk.vtkVolumeProperty()
    prop.SetColor(color_tf)
    prop.SetScalarOpacity(opacity_tf)
    prop.SetInterpolationTypeToLinear()
    prop.ShadeOff()

    mapper: vtk.vtkSmartVolumeMapper = vtk.vtkSmartVolumeMapper()
    mapper.SetInputData(vtk_img)

    volume: vtk.vtkVolume = vtk.vtkVolume()
    volume.SetMapper(mapper)
    volume.SetProperty(prop)
    return volume


def compute_metrics(seg1: ITKImage, seg2: ITKImage) -> tuple[float, ...]:
    """
    Computes the metrics corresponding to the segmentation masks
    """
    a1: np.ndarray = (itk.array_from_image(seg1) > 0).astype(np.uint8)
    a2: np.ndarray = (itk.array_from_image(seg2) > 0).astype(np.uint8)
    spacing: tuple[float, ...] = seg1.GetSpacing()
    vox: float = spacing[0] * spacing[1] * spacing[2]
    v1, v2 = a1.sum() * vox, a2.sum() * vox
    delta, pct = v2 - v1, (v2 - v1) / v1 * 100 if v1 > 0 else 0.0
    return v1, v2, delta, pct


def make_label(text: str, x: float, y: float) -> vtk.vtkTextActor:
    """
    Creates a text actor with the given text and positions
    """
    a: vtk.vtkTextActor = vtk.vtkTextActor()
    a.SetInput(text)
    a.GetTextProperty().SetFontSize(16)
    a.GetTextProperty().SetColor(1.0, 1.0, 1.0)
    a.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
    a.SetPosition(x, y)
    return a


def itk_user_transform(itk_img: ITKImage) -> vtk.vtkTransform:
    """
    Build the vtkTransform that encodes ITK's direction + origin.
    """
    direction: np.ndarray = itk.array_from_matrix(itk_img.GetDirection())
    origin: np.ndarray = np.array(itk_img.GetOrigin())
    spacing: np.ndarray = np.array(itk_img.GetSpacing())

    mat: vtk.vtkMatrix4x4 = vtk.vtkMatrix4x4()
    for i in range(3):
        for j in range(3):
            mat.SetElement(i, j, direction[i, j] * spacing[j])
    mat.SetElement(0, 3, origin[0])
    mat.SetElement(1, 3, origin[1])
    mat.SetElement(2, 3, origin[2])
    mat.SetElement(3, 3, 1.0)

    transform: vtk.vtkTransform = vtk.vtkTransform()
    transform.SetMatrix(mat)
    return transform


def visualize_simple(
    ct1_path: str,
    ct2_path: str,
    mask1_path: str,
    mask2_path: str,
) -> None:
    """
    Affiche T1 a gauche et T2 a droite : crane en volume + tumeur en surface.
    """
    ct1 = load_image(ct1_path)
    ct2 = load_image(ct2_path)
    seg1 = load_image(mask1_path)
    seg2 = load_image(mask2_path)

    vol1 = make_volume_actor(itk_ct_to_vtk_ct(ct1))
    vol2 = make_volume_actor(itk_ct_to_vtk_ct(ct2))
    actor1 = make_surface_actor(itk_image_to_vtk_image(seg1), (1.0, 0.08, 0.08), 0.95)
    actor2 = make_surface_actor(itk_image_to_vtk_image(seg2), (0.0, 0.8, 1.0), 0.95)

    vol1.SetUserTransform(itk_user_transform(ct1))
    vol2.SetUserTransform(itk_user_transform(ct2))
    actor1.SetUserTransform(itk_user_transform(seg1))
    actor2.SetUserTransform(itk_user_transform(seg2))

    m1 = compute_metrics(seg1, seg2)  # (v1, v2, delta, pct)
    txt1 = f"T1\nVolume : {m1[0]:.1f} mm3"
    txt2 = f"T2\nVolume : {m1[1]:.1f} mm3\nChange : {m1[2]:+.1f} mm3 ({m1[3]:+.1f}%)"

    ren_left = vtk.vtkRenderer()
    ren_right = vtk.vtkRenderer()
    ren_left.SetViewport(0.0, 0.0, 0.5, 1.0)
    ren_right.SetViewport(0.5, 0.0, 1.0, 1.0)
    for r in (ren_left, ren_right):
        r.SetBackground(0.1, 0.1, 0.15)
        r.RemoveAllLights()
        light = vtk.vtkLight()
        light.SetLightTypeToHeadlight()
        light.SetIntensity(1.5)
        r.AddLight(light)

    ren_left.AddVolume(vol1)
    ren_left.AddActor(actor1)
    ren_right.AddVolume(vol2)
    ren_right.AddActor(actor2)

    ren_left.AddActor2D(make_label("T1 (baseline)", 0.02, 0.92))
    ren_right.AddActor2D(make_label("T2 (follow-up)", 0.52, 0.92))
    ren_left.AddActor2D(make_label(txt1, 0.02, 0.02))
    ren_right.AddActor2D(make_label(txt2, 0.52, 0.02))

    ren_left.ResetCamera()
    ren_right.ResetCamera()

    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(ren_left)
    render_window.AddRenderer(ren_right)
    render_window.SetWindowName("Tumor Evolution: T1 vs T2")
    render_window.SetSize(1600, 800)

    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)
    interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
    render_window.Render()
    interactor.Start()
