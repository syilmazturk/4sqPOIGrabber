# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FoursquarePOIGrabber
                                 A QGIS plugin
 A QGIS Plugin that fetches POIs via Foursquare API and displays as point layer.
                             -------------------
        begin                : 2016-01-26
        copyright            : (C) 2016 by Serhat YILMAZTURK
        email                : serhat@yilmazturk.info
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
    """Load FoursquarePOIGrabber class from file FoursquarePOIGrabber.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .foursquare_poi_grabber import FoursquarePOIGrabber
    return FoursquarePOIGrabber(iface)
