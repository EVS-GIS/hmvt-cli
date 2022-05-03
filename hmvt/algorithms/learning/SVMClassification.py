# -*- coding: utf-8 -*-

import otbApplication

from classes import CustomLogger


def SVMClassification(lab, sampleShapes, classifModel, confusionMatrix, ram=str(128), logger=None):
    '''
    :type lab: str
    :type sampleShapes: str
    :type classifModel: str
    :type confusionMatrix: str
    :type ram: str
    :type logger: CustomLogger
    '''
    if not logger:
        logger = CustomLogger("learning")

    # Paramétrage de base du classifier
    TrainImagesClassifier = otbApplication.Registry.CreateApplication(
        "TrainImagesClassifier")
    TrainImagesClassifier.SetParameterStringList(
        "io.il", [lab])
    TrainImagesClassifier.SetParameterStringList(
        "io.vd", [sampleShapes])
    TrainImagesClassifier.SetParameterString(
        "io.out", classifModel)
    TrainImagesClassifier.SetParameterFloat(
        "sample.mt", 1000)
    TrainImagesClassifier.SetParameterFloat(
        "sample.vtr", 0.75)
    TrainImagesClassifier.SetParameterString(
        "ram", ram)

    TrainImagesClassifier.UpdateParameters()
    TrainImagesClassifier.SetParameterStringList(
        "sample.vfn", ["class"])

    # Matrice de confusion (optionnel)
    TrainImagesClassifier.SetParameterString(
        "io.confmatout", confusionMatrix)

    # Paramétrage spécifique au SVM
    TrainImagesClassifier.SetParameterString(
        "classifier", "libsvm")
    TrainImagesClassifier.SetParameterString(
        "classifier.libsvm.k", "rbf")
    TrainImagesClassifier.SetParameterString(
        "classifier.libsvm.m", "csvc")
    TrainImagesClassifier.SetParameterFloat(
        "classifier.libsvm.c", 1)
    TrainImagesClassifier.SetParameterFloat(
        "classifier.libsvm.nu", 0.5)

    # Exécution du TrainImagesClassifier
    logger.message("learning from samples")
    TrainImagesClassifier.ExecuteAndWriteOutput()
    logger.message("learning finished")

    return