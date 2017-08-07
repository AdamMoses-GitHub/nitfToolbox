# -*- coding: utf-8 -*-
"""
/***************************************************************************
 nitfToolbox
                                 A QGIS plugin
 Tools and utilities for dealing with NITF (National Imagery Transmission Format) files.
                              -------------------
        begin                : 2017-08-01
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Adam Moses
        email                : adam.moses@nrl.navy.mil
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

# Import QT bits
from PyQt4 import QtGui
#from PyQt4.QtGui import QAction, QIcon, QFileDialog, QDialogButtonBox, QMessageBox, QTableWidgetItem
from PyQt4.QtGui import *
from PyQt4 import QtCore
from PyQt4.QtCore import *
# Import time
import time
# Improt QGIS bits
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from nitf_toolbox_dialog import nitfToolboxDialog
# Import os capabilities
import os.path
# Import gdal
import osgeo.gdal

# ---------------------------------------------

class nitfToolbox:
    """QGIS Plugin Implementation."""
    
# ---------------------------------------------      
         
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
            'nitfToolbox_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)       

        # Create the dialog (after translation) and keep reference
        self.exportDialog = nitfToolboxDialog()     
        QObject.connect(self.exportDialog.pushButton_chooseNITFFile, SIGNAL("clicked()"), self.chooseNITFFile)  
        QObject.connect(self.exportDialog.pushButton_chooseExportDirectory, SIGNAL("clicked()"), self.chooseExportPath)
        QObject.connect(self.exportDialog.pushButton_export, SIGNAL("clicked()"), self.exportSubdatasets)      
             
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&NITF Toolbox')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'nitfToolbox')
        self.toolbar.setObjectName(u'nitfToolbox')               
        
# ---------------------------------------------        
        
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
        return QCoreApplication.translate('nitfToolbox', message)

# ---------------------------------------------

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

# ---------------------------------------------       
        
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = ':/plugins/nitfToolbox/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Export NITF Subdatasets'),
            callback=self.startExportDialog,
            parent=self.iface.mainWindow())        

# ---------------------------------------------
            
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&NITF Toolbox'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

# ---------------------------------------------

    def chooseNITFFile(self):
        """Reacts on browse button"""
        settingsObj = QSettings()   
        startingPath = settingsObj.value("nitf_toolbox/exportNITFFileDefaultPath", "")
        nitfFileNameAndPath = QFileDialog.getOpenFileName(caption = "Open NITF File", filter = '*.ntf', directory = startingPath)
        if (nitfFileNameAndPath != ""):
            isValid = self.validateNITFFile(nitfFileNameAndPath)
            if isValid:
                settingsObj.setValue("nitf_toolbox/exportNITFFileDefaultPath", QFileInfo(nitfFileNameAndPath).canonicalPath())
                self.exportDialog.lineEdit_nitfFilename.setText(nitfFileNameAndPath)
                self.toggleExportDialog(True)
                self.setupNITFExport(nitfFileNameAndPath)
            else:
                self.exportDialog.lineEdit_nitfFilename.setText("") 
                self.toggleExportDialog(False)
                QMessageBox.information(None, "NITF Toolbox", "This does appear to be a valid NITF file.")

# ---------------------------------------------            
            
    def chooseExportPath(self):
        """Reacts on browse button"""
        exportPath = QFileDialog.getExistingDirectory(caption = "Choose Export Directory", directory = self.exportDialog.lineEdit_exportDirectory.text())
        self.exportDialog.lineEdit_exportDirectory.setText(exportPath)   
           
# ---------------------------------------------           
           
    def toggleExportDialog(self, isOn):
        if ( isOn ):
            self.exportDialog.label_subdatasets.setEnabled(True)
            self.exportDialog.listWidget_subdatasets.setEnabled(True)
            self.exportDialog.label_exportDirectory.setEnabled(True)
            self.exportDialog.lineEdit_exportDirectory.setEnabled(True)            
            self.exportDialog.pushButton_chooseExportDirectory.setEnabled(True)
            self.exportDialog.pushButton_export.setEnabled(True)
            self.exportDialog.checkBox_addToProject.setEnabled(True)
            self.exportDialog.checkBox_addToProject.setChecked(True)
            self.exportDialog.pushButton_export.setEnabled(True)
        else:
            self.exportDialog.lineEdit_exportDirectory.setText("")
            self.exportDialog.lineEdit_nitfFilename.setText("")
            self.exportDialog.listWidget_subdatasets.clear()
            self.exportDialog.label_subdatasets.setEnabled(False)
            self.exportDialog.listWidget_subdatasets.setEnabled(False)
            self.exportDialog.label_exportDirectory.setEnabled(False)
            self.exportDialog.lineEdit_exportDirectory.setEnabled(False)            
            self.exportDialog.pushButton_chooseExportDirectory.setEnabled(False)
            self.exportDialog.pushButton_export.setEnabled(False)
            self.exportDialog.checkBox_addToProject.setEnabled(False)
            self.exportDialog.checkBox_addToProject.setChecked(False)
            self.exportDialog.pushButton_export.setEnabled(False)        

# ---------------------------------------------

    def setupNITFExport(self, nitfFileNameAndPath):
        """Reacts on browse button"""
        nitfFile = osgeo.gdal.Open(nitfFileNameAndPath)                 
        nitfSubDatasets = nitfFile.GetSubDatasets()
        cSubDatasetIndex = 0
        for cSubDataset in nitfSubDatasets:
            (cName, cDesc) = cSubDataset
            item = QListWidgetItem(cDesc)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Checked)
            self.exportDialog.listWidget_subdatasets.addItem(item)
            #self.exportDialog.listWidget_subdatasets.addItem(cDesc)
            cSubDatasetIndex += 1
        nitfPath = QFileInfo(nitfFileNameAndPath).canonicalPath()
        self.exportDialog.lineEdit_exportDirectory.setText(nitfPath)        
            
# ---------------------------------------------
        
    def validateNITFFile(self, nitfFileNameAndPath):
        baseName = QFileInfo(nitfFileNameAndPath).baseName()
        testNITFLayer = QgsRasterLayer(nitfFileNameAndPath, baseName)
        isValid = True
        if not testNITFLayer.isValid():
            isValid = False
        else:
            testNITFOpen = osgeo.gdal.Open(nitfFileNameAndPath)
            testNITFDriver = testNITFOpen.GetDriver()
            testNITFDriverDescription = testNITFDriver.GetDescription()
            if ( testNITFDriverDescription != "NITF" ):
                isValid = False            
        return isValid
        
# ---------------------------------------------
        
    def exportSubdatasets(self):
        exportedFiles = []
        nitfFileNameAndPath = self.exportDialog.lineEdit_nitfFilename.text()   
        origFileName = QFileInfo(nitfFileNameAndPath).fileName()
        exportPath = self.exportDialog.lineEdit_exportDirectory.text()
        nitfFile = osgeo.gdal.Open(nitfFileNameAndPath)                 
        nitfSubDatasets = nitfFile.GetSubDatasets()
        cSubDatasetIndex = 0
        geotiffDriver = osgeo.gdal.GetDriverByName("GTiff")
        for cSubDataset in nitfSubDatasets:
            cSubDatasetIndex += 1
            curExportFilename = origFileName + '.sub' + str(cSubDatasetIndex).zfill(2) + '.tif'
            curFullFilename = exportPath + '/' + curExportFilename
            if ( ( self.exportDialog.listWidget_subdatasets.item(cSubDatasetIndex - 1).checkState() == QtCore.Qt.Checked ) & ( QFileInfo(curFullFilename).exists() == False ) ):
                (cName, cDesc) = cSubDataset
                cSubNITFFile = None
                cSubNITFFile = osgeo.gdal.Open(cName)
                cRasterBandsCount = cSubNITFFile.RasterCount            
                bandsArray = []
                for curBand in range(1, cRasterBandsCount + 1):
                    bandsArray.append(cSubNITFFile.GetRasterBand(curBand).ReadAsArray())
                cRasterBandDataType = cSubNITFFile.GetRasterBand(1).DataType
                [cColumns, cRows] = cSubNITFFile.GetRasterBand(1).ReadAsArray().shape  
                cOutputFile = geotiffDriver.Create(curFullFilename, cRows, cColumns, cRasterBandsCount, cRasterBandDataType )
                cOutputFile.SetGeoTransform(nitfFile.GetGeoTransform())
                cOutputFile.SetProjection(nitfFile.GetProjection())
                for curBand in range(1, cRasterBandsCount + 1):
                    cOutputFile.GetRasterBand(curBand).WriteArray(bandsArray[curBand - 1])
                cOutputFile.FlushCache()
                cOutputFile = None
                cSubNITFFile = None
                exportedFiles.append(curFullFilename)
                time.sleep(0.1)
        if ( self.exportDialog.checkBox_addToProject.isChecked() == True ):
            for cFilename in reversed(exportedFiles):
                shortName = QFileInfo(cFilename).fileName()
                curLayer = QgsRasterLayer(cFilename, shortName)
                QgsMapLayerRegistry.instance().addMapLayer(curLayer)
                time.sleep(0.1)
        geotiffDriver = None
  
        
# ---------------------------------------------
        
    def startExportDialog(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.toggleExportDialog(False)
        self.exportDialog.show()
        # Run the dialog event loop
        result = self.exportDialog.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
                
# ---------------------------------------------



