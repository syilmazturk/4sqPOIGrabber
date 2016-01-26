# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FoursquarePOIGrabber
                                 A QGIS plugin
 A QGIS Plugin that fetches POIs via Foursquare API and displays as point layer.
                              -------------------
        begin                : 2016-01-26
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Serhat YILMAZTURK
        email                : serhat@yilmazturk.info
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QUrl, QObject, pyqtSlot
from PyQt4.QtGui import QAction, QIcon

# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from foursquare_poi_grabber_dialog import FoursquarePOIGrabberDialog
import os.path


class Foo(QObject):
    @pyqtSlot(str, result=str)
    def get_lat(self, value):
        global lat_value
        lat_value = value
        return lat_value

    @pyqtSlot(str, result=str)
    def get_lon(self, value):
        global lon_value
        lon_value = value
        return lon_value


class FoursquarePOIGrabber:
    """QGIS Plugin Implementation."""
    def enableJavaScript(self):
        self.dlg.webView_gmap.page().mainFrame().addToJavaScriptWindowObject("foo", self.foo)

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface

        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'FoursquarePOIGrabber_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = FoursquarePOIGrabberDialog()
        self.foo = Foo()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&4sq POI Grabber')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'FoursquarePOIGrabber')
        self.toolbar.setObjectName(u'FoursquarePOIGrabber')

        self.dlg.webView_gmap.loadFinished.connect(self.enableJavaScript)
        self.dlg.webView_gmap.load(QUrl('http://yilmazturk.info/ankageo/gmap.html'))

        self.dlg.pushButton_fetchPOI.clicked.connect(self.hacilar)

    def hacilar(self):
        self.dlg.lineEdit_clientID.setText(lat_value)
        self.dlg.lineEdit_clientSecret.setText(lon_value)
        print lat_value
        print lon_value

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('FoursquarePOIGrabber', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/FoursquarePOIGrabber/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'4sq POI Grabber'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&4sq POI Grabber'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            pass
            # Do something useful here - delete the line containing pass and
            # substitute with your code.

