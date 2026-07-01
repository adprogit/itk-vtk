import os
from typing import Any, TypeAlias

import itk
import matplotlib.pyplot as plt
import numpy as np

ImageType: TypeAlias = itk.Image[itk.F, 3]

# path_1 = "../data/case6_gre1.nrrd"
# path_2 = "../data/case6_gre2.nrrd"


ITKImage: TypeAlias = Any
ITKTransform: TypeAlias = Any
ITKMetric: TypeAlias = Any


def read_volumes(path: str, path2: str) -> tuple[ITKImage, ITKImage]:
    pixel_type = itk.F
    img1 = itk.imread(path, pixel_type)
    img2 = itk.imread(path2, pixel_type)
    return img1, img2


def _centre_geometrique(image: ITKImage) -> Any:
    region = image.GetLargestPossibleRegion()
    size = region.GetSize()
    index = itk.ContinuousIndex[itk.D, 3]()
    for i in range(3):
        index[i] = (size[i] - 1) / 2.0
    return image.TransformContinuousIndexToPhysicalPoint(index)


def _initialiser_centre(transform: ITKTransform, fixed: ITKImage, moving: ITKImage) -> None:
    cf = _centre_geometrique(fixed)
    cm = _centre_geometrique(moving)
    transform.SetCenter(cf)
    translation = transform.GetTranslation()
    for i in range(3):
        translation[i] = cm[i] - cf[i]
    transform.SetTranslation(translation)


def recaler_rigide(
    fixed: ITKImage, moving: ITKImage, iterations: int = 200
) -> tuple[ITKImage, ITKImage]:
    FixedType, MovingType = type(fixed), type(moving)
    transform = itk.VersorRigid3DTransform[itk.D].New()
    init = itk.CenteredTransformInitializer[type(transform), FixedType, MovingType].New(
        Transform=transform, FixedImage=fixed, MovingImage=moving
    )
    init.GeometryOn()
    init.InitializeTransform()

    metric = itk.MeanSquaresImageToImageMetricv4[FixedType, MovingType].New()

    optimizer = itk.RegularStepGradientDescentOptimizerv4[itk.D].New()
    optimizer.SetLearningRate(4.0)
    optimizer.SetMinimumStepLength(1e-4)
    optimizer.SetRelaxationFactor(0.5)
    optimizer.SetNumberOfIterations(iterations)
    scales = itk.RegistrationParameterScalesFromPhysicalShift[type(metric)].New()
    scales.SetMetric(metric)
    optimizer.SetScalesEstimator(scales)

    registration = itk.ImageRegistrationMethodv4[FixedType, MovingType].New(
        FixedImage=fixed,
        MovingImage=moving,
        Metric=metric,
        Optimizer=optimizer,
        InitialTransform=transform,
    )
    registration.Update()
    final = registration.GetTransform()

    resampler = itk.ResampleImageFilter.New(
        Input=moving,
        Transform=final,
        UseReferenceImage=True,
        ReferenceImage=fixed,
        DefaultPixelValue=0,
    )
    resampler.Update()
    return resampler.GetOutput(), final


def recaler_translation(
    fixed: ITKImage, moving: ITKImage, iterations: int = 200
) -> tuple[ITKImage, ITKTransform]:
    FixedType, MovingType = type(fixed), type(moving)
    transform = itk.TranslationTransform[itk.D, 3].New()
    metric = itk.MeanSquaresImageToImageMetricv4[FixedType, MovingType].New()
    optimizer = itk.RegularStepGradientDescentOptimizerv4[itk.D].New()
    optimizer.SetLearningRate(4.0)
    optimizer.SetMinimumStepLength(1e-4)
    optimizer.SetRelaxationFactor(0.5)
    optimizer.SetNumberOfIterations(iterations)
    scales = itk.RegistrationParameterScalesFromPhysicalShift[type(metric)].New()
    scales.SetMetric(metric)
    optimizer.SetScalesEstimator(scales)
    registration = itk.ImageRegistrationMethodv4[FixedType, MovingType].New(
        FixedImage=fixed,
        MovingImage=moving,
        Metric=metric,
        Optimizer=optimizer,
        InitialTransform=transform,
    )
    registration.Update()
    final = registration.GetTransform()
    resampler = itk.ResampleImageFilter.New(
        Input=moving,
        Transform=final,
        UseReferenceImage=True,
        ReferenceImage=fixed,
        DefaultPixelValue=0,
    )
    resampler.Update()
    return resampler.GetOutput(), final


def recaler_similarity(
    fixed: ITKImage, moving: ITKImage, iterations: int = 200
) -> tuple[ITKImage, ITKTransform]:
    FixedType, MovingType = type(fixed), type(moving)
    transform = itk.Similarity3DTransform[itk.D].New()
    _initialiser_centre(transform, fixed, moving)
    metric = itk.MeanSquaresImageToImageMetricv4[FixedType, MovingType].New()
    optimizer = itk.RegularStepGradientDescentOptimizerv4[itk.D].New()
    optimizer.SetLearningRate(4.0)
    optimizer.SetMinimumStepLength(1e-4)
    optimizer.SetRelaxationFactor(0.5)
    optimizer.SetNumberOfIterations(iterations)
    scales = itk.RegistrationParameterScalesFromPhysicalShift[type(metric)].New()
    scales.SetMetric(metric)
    optimizer.SetScalesEstimator(scales)
    registration = itk.ImageRegistrationMethodv4[FixedType, MovingType].New(
        FixedImage=fixed,
        MovingImage=moving,
        Metric=metric,
        Optimizer=optimizer,
        InitialTransform=transform,
    )
    registration.Update()
    final = registration.GetTransform()
    resampler = itk.ResampleImageFilter.New(
        Input=moving,
        Transform=final,
        UseReferenceImage=True,
        ReferenceImage=fixed,
        DefaultPixelValue=0,
    )
    resampler.Update()
    return resampler.GetOutput(), final


def recaler_affine(
    fixed: ITKImage, moving: ITKImage, iterations: int = 200
) -> tuple[ITKImage, ITKTransform]:
    FixedType, MovingType = type(fixed), type(moving)
    transform = itk.AffineTransform[itk.D, 3].New()
    _initialiser_centre(transform, fixed, moving)
    metric = itk.MeanSquaresImageToImageMetricv4[FixedType, MovingType].New()
    optimizer = itk.RegularStepGradientDescentOptimizerv4[itk.D].New()
    optimizer.SetLearningRate(4.0)
    optimizer.SetMinimumStepLength(1e-4)
    optimizer.SetRelaxationFactor(0.5)
    optimizer.SetNumberOfIterations(iterations)
    scales = itk.RegistrationParameterScalesFromPhysicalShift[type(metric)].New()
    scales.SetMetric(metric)
    optimizer.SetScalesEstimator(scales)
    registration = itk.ImageRegistrationMethodv4[FixedType, MovingType].New(
        FixedImage=fixed,
        MovingImage=moving,
        Metric=metric,
        Optimizer=optimizer,
        InitialTransform=transform,
    )
    registration.Update()
    final = registration.GetTransform()
    resampler = itk.ResampleImageFilter.New(
        Input=moving,
        Transform=final,
        UseReferenceImage=True,
        ReferenceImage=fixed,
        DefaultPixelValue=0,
    )
    resampler.Update()
    return resampler.GetOutput(), final


PLANS = {"sagittal": 0, "coronal": 1, "axial": 2}


def sauver_volumes(
    recalee: ITKImage,
    transform: ITKTransform | None = None,
    prefixe: str = "recale",
    dossier: str = "results",
) -> str:
    os.makedirs(dossier, exist_ok=True)
    chemin = os.path.join(dossier, f"{prefixe}.nrrd")
    itk.imwrite(recalee, chemin)
    print(f"écrit : {chemin}")
    if transform is not None:
        chemin_tfm = os.path.join(dossier, f"{prefixe}.tfm")
        itk.transformwrite([transform], chemin_tfm)
        print(f"écrit : {chemin_tfm}")
    return chemin


def sauver_coupes(
    fixed: ITKImage,
    moving: ITKImage,
    recalee: ITKImage,
    prefixe: str = "recalage",
    dossier: str = "figures",
) -> None:
    os.makedirs(dossier, exist_ok=True)
    f = itk.array_view_from_image(fixed)
    m = itk.array_view_from_image(moving)
    r = itk.array_view_from_image(recalee)

    for nom, axe in PLANS.items():
        coupe = f.shape[axe] // 2
        fs = np.take(f, coupe, axis=axe)
        ms = np.take(m, coupe, axis=axe)
        rs = np.take(r, coupe, axis=axe)

        fig, ax = plt.subplots(1, 3, figsize=(15, 5))
        ax[0].imshow(np.abs(fs - ms), cmap="gray")
        ax[0].set_title(f"Différence AVANT — {nom}")
        ax[1].imshow(np.abs(fs - rs), cmap="gray")
        ax[1].set_title(f"Différence APRÈS — {nom}")
        ax[2].imshow(fs, cmap="Reds", alpha=0.5)
        ax[2].imshow(rs, cmap="Blues", alpha=0.5)
        ax[2].set_title(f"Superposition — {nom}")
        for a in ax:
            a.axis("off")
        plt.tight_layout()
        chemin = os.path.join(dossier, f"{prefixe}_{nom}.png")
        fig.savefig(chemin, dpi=120, bbox_inches="tight")
        plt.close(fig)
        print(f"écrit : {chemin}")


def mesurer_residu(fixed: ITKImage, autre: ITKImage) -> float:
    f = itk.array_view_from_image(fixed).astype(np.float64)
    a = itk.array_view_from_image(autre).astype(np.float64)
    return float(np.sqrt(np.mean((f - a) ** 2)))


def recaler(path_1: str, path_2: str) -> str:
    fixed, moving = read_volumes(path_1, path_2)
    recalee, transform = recaler_rigide(fixed, moving)
    return sauver_volumes(recalee, transform, prefixe="recale_rigide")
