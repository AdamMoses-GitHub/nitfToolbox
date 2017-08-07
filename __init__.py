# -*- coding: utf-8 -*-
"""
/***************************************************************************
 nitfToolbox
                                 A QGIS plugin
 Tools and utilities for dealing with NITF (National Imagery Transmission Format) files.
                             -------------------
        begin                : 2017-08-01
        copyright            : (C) 2017 by Adam Moses
        email                : adam.moses@nrl.navy.mil
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load nitfToolbox class from file nitfToolbox.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .nitf_toolbox import nitfToolbox
    return nitfToolbox(iface)
