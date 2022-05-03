# -*- coding: utf-8 -*-

import os
import otbApplication


def computeClassif(img, model, img_out, memory, logger, mask=None):
    """
    :type img: str
    :type model: str
    :type img_out: str
    :type memory: str
    :type logger: CustomLogger
    :type mask: str
    """
    ImagesClassifier = otbApplication.Registry.CreateApplication("ImageClassifier")
    ImagesClassifier.SetParameterString("in", img)
    ImagesClassifier.SetParameterString("model", model)
    ImagesClassifier.SetParameterString("out", img_out)
    ImagesClassifier.SetParameterString("ram", memory)

    # Masquer la BA si demandé
    if mask:
        if not os.path.isfile(mask):
            logger.message("mask file doesn't exist")
        else:
            ImagesClassifier.SetParameterString("mask", mask)

    # Appliquer la classif
    logger.message("classification")
    ImagesClassifier.ExecuteAndWriteOutput()
