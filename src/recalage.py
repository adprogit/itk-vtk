import os
from typing import Any, TypeAlias

import itk
import matplotlib.pyplot as plt
import numpy as np

ImageType: TypeAlias = itk.Image[itk.F, 3]

path_1 = "../data/case6_gre1.nrrd"
path_2 = "../data/case6_gre2.nrrd"


ITKImage: TypeAlias = Any
ITKTransform: TypeAlias = Any
ITKMetric: TypeAlias = Any


def read_volumes(path: str, path2: str) -> tuple[ITKImage, ITKImage]:
    pixel_type = itk.F
    img1 = itk.imread(path, pixel_type)
    img2 = itk.imread(path2, pixel_type)
    return img1, img2


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


PLANS = {"axial": 0, "coronal": 1, "sagittal": 2}


def sauver_coupes(fixed, moving, recalee, prefixe="recalage", dossier="figures"):
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


def main() -> int:
    fixed, moving = read_volumes(path_1, path_2)
    fixed_r, moving_r = recaler_rigide(fixed, moving)
    itk.imwrite(fixed_r, "recalee.png")
    print(moving_r.GetParameters())
    return 0


fixed, moving = read_volumes(path_1, path_2)
recalee, transform = recaler_rigide(fixed, moving)
sauver_coupes(fixed, moving, recalee)
