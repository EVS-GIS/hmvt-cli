# -*- coding: utf-8 -*-

import rasterio
from numpy import count_nonzero

from classes import CustomLogger


def makeReport(mask_file, map_name, logger):
    '''
    Ecriture du rapport final (etapes de traitement exécutées et timer)
    '''
    report_logger = CustomLogger("FinalLogs")

    with rasterio.open(mask_file) as src:
        logger.message("computing surface of the fluvial corridor extracted")

        msk = src.read(1)
        src.close()

        npx = count_nonzero(msk)
        del msk

        time_per_px = logger.timer/float(npx)

        logger.message("writing final report on FinalLogs file")
        report_logger.message(";{mp};{px};{stp};{tm};{tmpx}".format(
                              mp=map_name, px=str(npx), stp=str(logger.steps), tm=logger.txtTimer, tmpx=str(time_per_px)))

    return
