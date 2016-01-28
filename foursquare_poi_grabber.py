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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QUrl, QObject, pyqtSlot, QVariant
from PyQt4.QtGui import QAction, QIcon, QIntValidator, QValidator
from qgis.core import QgsVectorLayer, QgsField, QgsGeometry, QgsPoint, QgsFeature, QgsMapLayerRegistry
from qgis.gui import QgsMessageBar
from qgis.utils import iface
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from foursquare_poi_grabber_dialog import FoursquarePOIGrabberDialog
import datetime
import urllib2
import json
import os.path


class Foo(QObject):
    @pyqtSlot(str, result=str)
    def get_lat(self, value):
        global lat
        lat = value
        return lat

    @pyqtSlot(str, result=str)
    def get_lon(self, value):
        global lon
        lon = value
        return lon


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
        global validator
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

        validator = QIntValidator()
        self.dlg.lineEdit_radius.setValidator(validator)
        self.dlg.lineEdit_radius.setMaxLength(6)
        self.dlg.lineEdit_radius.textChanged.connect(self.check_state)
        self.dlg.lineEdit_radius.editingFinished.connect(self.check_radius)

        self.dlg.webView_gmap.loadFinished.connect(self.enableJavaScript)
        self.dlg.webView_gmap.load(QUrl('http://yilmazturk.info/poigrabber/gmap.html'))

        self.dlg.pushButton_fetchPOI.clicked.connect(self.get_poi)

        self.populate_combobox()

    def check_state(self):
        state = validator.validate(self.dlg.lineEdit_radius.text(), 0)[0]
        if state == QValidator.Acceptable:
            color = '#c4df9b'
            self.dlg.lineEdit_radius.setStyleSheet('QLineEdit { background-color: %s }' % color)
        elif state == QValidator.Intermediate:
            color = '#fff79a'
            self.dlg.lineEdit_radius.setStyleSheet('QLineEdit { background-color: %s }' % color)
        else:
            color = '#f6989d'
            self.dlg.lineEdit_radius.setStyleSheet('QLineEdit { background-color: %s }' % color)

    def check_radius(self):
        if int(self.dlg.lineEdit_radius.text()) > 100000:
            color = '#f6989d'
            self.dlg.lineEdit_radius.setStyleSheet('QLineEdit { background-color: %s }' % color)
            iface.messageBar().pushMessage(u"Error:", u" The maximum supported radius is currently 100,000 meters.",
                                           level=QgsMessageBar.CRITICAL, duration=5)
        else:
            pass

    def get_poi(self):
        try:
            client_id = self.dlg.lineEdit_clientID.text()
            client_secret = self.dlg.lineEdit_clientSecret.text()
            radius = self.dlg.lineEdit_radius.text()
            category_name = self.dlg.comboBox_category.currentText()
            category_id = foursquare_categories[category_name]
            current_date = str(datetime.datetime.now().date()).replace("-", "")
            url = "https://api.foursquare.com/v2/venues/search?ll=%s,%s&radius=%s&intent=browse&categoryId=%s&limit=50&client_id=%s&client_secret=%s&v=%s" % (lat, lon, radius, category_id, client_id, client_secret, current_date)

            req = urllib2.Request(url)
            opener = urllib2.build_opener()
            f = opener.open(req)
            data = json.loads(f.read())

            json_object_count = len(data['response']['venues'])

            if json_object_count == 0:
                iface.messageBar().pushMessage(u"Info:", "Unfortunately, there is no POI at the specified location...",
                                               level=QgsMessageBar.INFO, duration=5)
            else:
                iface.messageBar().pushMessage(u"Info:", str(json_object_count) + " POI(s) fetched for " +
                                               category_name + " category", level=QgsMessageBar.SUCCESS, duration=5)

                poi_id = []
                poi_name = []
                poi_lon = []
                poi_lat = []

                for i in range(0, json_object_count):
                    poi_id.append(data['response']['venues'][i]['id'])
                    poi_name.append(data['response']['venues'][i]['name'])
                    poi_lon.append(data['response']['venues'][i]['location']['lng'])
                    poi_lat.append(data['response']['venues'][i]['location']['lat'])

                coord_pairs = []

                layer_name = "POI - %s" % category_name
                memory_layer = QgsVectorLayer("Point?crs=epsg:4326", layer_name, "memory")
                memory_layer.startEditing()
                provider = memory_layer.dataProvider()
                provider.addAttributes([QgsField("FoursqID", QVariant.String), QgsField("Name",  QVariant.String), QgsField("Category", QVariant.String), QgsField("Date", QVariant.String)])

                for fsid, name, x, y in zip(poi_id, poi_name, poi_lon, poi_lat):
                    geometry = QgsGeometry.fromPoint(QgsPoint(x, y))
                    feature = QgsFeature()
                    feature.setGeometry(geometry)
                    feature.setAttributes([fsid, name, category_name, current_date])
                    coord_pairs.append(feature)

                memory_layer.dataProvider().addFeatures(coord_pairs)
                memory_layer.updateExtents()
                memory_layer.commitChanges()
                QgsMapLayerRegistry.instance().addMapLayer(memory_layer)
        except:
            iface.messageBar().pushMessage(u"Error:", "Please make sure to drop a pin on Google Map or fill in all \
                                            the fields!", level=QgsMessageBar.CRITICAL, duration=5)


    def populate_combobox(self):
        global foursquare_categories
        foursquare_categories = {
            "Medical - Hospital": "4bf58dd8d48988d196941735",
            "Medical - Dentist's Office": "4bf58dd8d48988d178941735",
            "Medical - Veterinarian": "4d954af4a243a5684765b473",
            "Education - University": "4bf58dd8d48988d1ae941735",
            "Education - High School": "4bf58dd8d48988d13d941735",
            "Education - Elementary School": "4f4533804b9074f6e4fb0105",
            "Culture & Arts - Museum": "4bf58dd8d48988d181941735",
            "Culture & Arts - Theater": "4bf58dd8d48988d137941735",
            "Culture & Arts - Movie Theater": "4bf58dd8d48988d17f941735",
            "Food": "4d4b7105d754a06374d81259",
            "Food - Cafe": "4bf58dd8d48988d16d941735",
            "Food - Bar": "4bf58dd8d48988d116941735",
            "Office": "4bf58dd8d48988d124941735",
            "Finance - ATM": "52f2ab2ebcbc57f1066b8b56",
            "Finance - Bank": "4bf58dd8d48988d10a951735",
            "Spiritual - Mosque": "4bf58dd8d48988d138941735",
            "Spiritual - Church": "4bf58dd8d48988d132941735",
            "Spiritual - Synagogue": "4bf58dd8d48988d139941735",
            "Hotel": "4bf58dd8d48988d1fa931735",
            "Service - Gas Station": "4bf58dd8d48988d113951735",
            "Service - Supermarket": "52f2ab2ebcbc57f1066b8b46",
            "Service - Barbershop": "4bf58dd8d48988d110951735",
            "Service - Laundry Service": "4bf58dd8d48988d1fc941735",
            "Service - Car Wash": "4f04ae1f2fb6e1c99f3db0ba",
            "Service - Rental Car": "4bf58dd8d48988d1ef941735",
            "Transport - Bus Stop": "52f2ab2ebcbc57f1066b8b4f",
            "Transport - Metro Station": "4bf58dd8d48988d1fd931735",
            "Transport - Tram Station": "52f2ab2ebcbc57f1066b8b51",
            "Transport - Taxi": "4bf58dd8d48988d130951735",
            "Transport - Parking": "4c38df4de52ce0d596b336e1"
        }

        category_list = []
        for category in foursquare_categories.keys():
            category_list.append(category)
        self.dlg.comboBox_category.addItems(sorted(category_list))

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

