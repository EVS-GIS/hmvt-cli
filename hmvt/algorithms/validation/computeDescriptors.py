# -*- coding: utf-8 -*-

import pandas as pd


def computeDescriptors(confmat, logger):
    if not logger:
        from CustomLogger import CustomLogger
        logger = CustomLogger("validation")


    logger.message("computing accuracy descriptors for: "+str(confmat))

    mat = pd.read_csv(confmat, sep=",", header=1)

    if(len(mat.index) == 3):
        mat.index = ["ref_water", "ref_banks", "ref_vegetation"]
    else:
        logger.message(
            "reference format unrecognized, descriptors not computed", console=True, warning=True)
        return

    if(len(mat.columns) == 5):
        # Cas d'une matrice de confusion de couches de couleurs
        mat_type = "color layers"

        mat.columns = ["prod_black", "prod_white",
                       "prod_blue", "prod_green", "prod_bistre"]

        # Calcul des précisions
        blue_TP = mat.loc["ref_water", "prod_blue"]
        blue_sum = sum(mat.loc[:, "prod_blue"])
        blue_prec = blue_TP/float(blue_sum)

        blue_bk_TP = mat.loc["ref_banks", "prod_blue"]

        green_TP = mat.loc["ref_vegetation", "prod_green"]
        green_sum = sum(mat.loc[:, "prod_green"])
        green_prec = green_TP/float(green_sum)

        # Calcul des rappels
        water_sum = sum(mat.loc["ref_water", :])
        bank_sum = sum(mat.loc["ref_banks", :])
        veget_sum = sum(mat.loc["ref_vegetation", :])

        water_rcl = blue_TP/float(water_sum)
        banks_rcl = blue_bk_TP/float(bank_sum)
        veget_rcl = green_TP/float(veget_sum)

        mat.loc["precision", :] = ["NaN", "NaN", blue_prec, green_prec, "NaN"]
        mat = mat.assign(recall=[water_rcl, banks_rcl, veget_rcl, "NaN"])

    elif(len(mat.columns) == 4):
        # Cas d'une matrice de confusion d'objets reconstruits
        mat_type = "objects"

        mat.columns = ["prod_water", "prod_banks",
                       "prod_vegetation", "prod_linear"]

        # Calcul des précisions
        water_TP = mat.loc["ref_water", "prod_water"]
        prod_water_sum = sum(mat.loc[:, "prod_water"])
        water_prec = water_TP/float(prod_water_sum)

        banks_TP = mat.loc["ref_banks", "prod_banks"]
        prod_banks_sum = sum(mat.loc[:, "prod_banks"])
        banks_prec = banks_TP/float(prod_banks_sum)

        vegetation_TP = mat.loc["ref_vegetation", "prod_vegetation"]
        prod_vegetation_sum = sum(mat.loc[:, "prod_vegetation"])
        vegetation_prec = vegetation_TP/float(prod_vegetation_sum)

        # Calcul des rappels
        ref_water_sum = sum(mat.loc["ref_water", :])
        ref_banks_sum = sum(mat.loc["ref_banks", :])
        ref_vegetation_sum = sum(mat.loc["ref_vegetation", :])

        water_rcl = water_TP/float(ref_water_sum)
        banks_rcl = banks_TP/float(ref_banks_sum)
        vegetation_rcl = vegetation_TP/float(ref_vegetation_sum)

        mat.loc["precision", :] = [water_prec,
                                   banks_prec, vegetation_prec, "NaN"]
        mat = mat.assign(recall=[water_rcl, banks_rcl, vegetation_rcl, "NaN"])

    else:
        logger.message(
            "produced format unrecognized, descriptors not computed", console=True, warning=True)
        return

    mat.to_csv(confmat)

    # Log du résultat de la validation
    logger.message(mat_type+" results:\n"+str(mat), console=True)

    return
