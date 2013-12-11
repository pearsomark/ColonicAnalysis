import os
import unittest
from __main__ import vtk, qt, ctk, slicer
import numpy as np


#
# ColonicAnalysis
#

class ColonicAnalysis:
  def __init__(self, parent):
    parent.title = "ColonicAnalysis" # TODO make this more human readable by adding spaces
    parent.categories = ["Examples"]
    parent.dependencies = []
    parent.contributors = ["Mark Pearson (CRGH)"] # replace with "Firstname Lastname (Org)"
    parent.helpText = """
    This is a scripted loadable module for analysing Colonic Transit studies.
    """
    parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc. and Steve Pieper, Isomics, Inc.  and was partially funded by NIH grant 3P41RR013218-12S1.
    Modified for Colonic Transit Analysis by Mark Pearson.
""" # replace with organization, grant and thanks.
    self.parent = parent

    import inspect
    modName = inspect.getframeinfo(inspect.currentframe())[0]
    lsep = modName.rindex('/')
    self.modPath = modName[0:lsep]
    parent.icon = qt.QIcon(self.modPath + '/Resources/Icons/Colon128.png')

    if slicer.mrmlScene.GetTagByClassName( "vtkMRMLScriptedModuleNode" ) != 'ScriptedModule':
      slicer.mrmlScene.RegisterNodeClass(vtkMRMLScriptedModuleNode())

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['ColonicAnalysis'] = self.runTest

  def runTest(self):
    tester = ColonicAnalysisTest()
    tester.runTest()

#
# qColonicAnalysisWidget
#

#class colonicUtil(object):



class ColonicAnalysisWidget:
  def __init__(self, parent = None):
    self.fileName = None
    self.fileDialog = None
    self.renderType = ('TH', 'threshold')
    self.parameterNode = None
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()
    self.updateParameterNode(self.parameterNode, vtk.vtkCommand.ModifiedEvent)
    self.setMRMLDefaults()

  def setup(self):
    # Instantiate and connect widgets ...

    #
    # Reload and Test area
    #
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)
    reloadCollapsibleButton.setChecked(False)

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "ColonicAnalysis Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    # reload and test button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadAndTestButton = qt.QPushButton("Reload and Test")
    self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
    reloadFormLayout.addWidget(self.reloadAndTestButton)
    self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

    #
    # preprocess area
    #
    preprocessCollapsibleButton = ctk.ctkCollapsibleButton()
    preprocessCollapsibleButton.text = "Preprocess"
    self.layout.addWidget(preprocessCollapsibleButton)
    preprocessFormLayout = qt.QFormLayout(preprocessCollapsibleButton)
    # fix volumes button
    self.fixvolumesButton = qt.QPushButton("Fix Volumes")
    preprocessFormLayout.addRow(self.fixvolumesButton)
    self.thresholdButton = qt.QPushButton("Calculate Thresholds")
    preprocessFormLayout.addRow(self.thresholdButton)
    # threshold scroller
    self.slider = ctk.ctkSliderWidget()
    self.slider.decimals = 0
    self.slider.enabled = False
    preprocessFormLayout.addRow("Threshold", self.slider)
    self.fixvolumesButton.connect('clicked()', self.onFixvolumes)
    self.thresholdButton.connect('clicked()', self.onCalcThresholds)
    preprocessCollapsibleButton.setChecked(False)
    # refresh button
    self.refreshButton = qt.QPushButton("Refresh")
    preprocessFormLayout.addRow(self.refreshButton)
    self.refreshButton.connect('clicked()', self.onTresholdRefresh)
    self.editorButton = qt.QPushButton("Create Labels")
    preprocessFormLayout.addRow(self.editorButton)
    self.editorButton.connect('clicked()', self.onCreateLabels)


    #
    # Volume manipulation area
    #
    scrollingCollapsibleButton = ctk.ctkCollapsibleButton()
    scrollingCollapsibleButton.text = "Volumes"
    self.layout.addWidget(scrollingCollapsibleButton)
    # Layout within the scrolling collapsible button
    scrollingFormLayout = qt.QFormLayout(scrollingCollapsibleButton)


    # make an instance of the logic for use by the slots
    self.logic = ColonicAnalysisLogic()

    self.radioButtonsFrame = qt.QFrame(self.parent)
    self.radioButtonsFrame.setLayout(qt.QHBoxLayout())
    scrollingFormLayout.addWidget(self.radioButtonsFrame)
    
    self.viewRadioFrame = qt.QFrame(self.parent)
    self.viewRadioFrame.setLayout(qt.QVBoxLayout())
    self.radioButtonsFrame.layout().addWidget(self.viewRadioFrame)
    
    self.viewRadioLabel = qt.QLabel("Change View: ", self.viewRadioFrame)
    self.viewRadioLabel.setToolTip( "Select the 6, 24 or 32 Hour data set")
    self.viewRadioFrame.layout().addWidget(self.viewRadioLabel)

    #self.radioSubFrame = qt.QFrame(self.viewRadioFrame)
    #self.selectLayout = qt.QGridLayout()
    #self.radioSubFrame.setLayout(self.selectLayout)
    self.r6HRSButton = qt.QRadioButton("6 Hours", self.viewRadioFrame)
    self.r24HRSButton = qt.QRadioButton("24 Hours", self.viewRadioFrame)
    self.r32HRSButton = qt.QRadioButton("32 Hours", self.viewRadioFrame)
    self.r6HRSButton.checked = True
    self.viewRadioFrame.layout().addWidget(self.r6HRSButton, 1, 0)
    self.viewRadioFrame.layout().addWidget(self.r24HRSButton, 0, 0)
    self.viewRadioFrame.layout().addWidget(self.r32HRSButton, 0, 0)
    self.r6HRSButton.connect('clicked()', self.onView6hr)
    self.r24HRSButton.connect('clicked()', self.onView24hr)
    self.r32HRSButton.connect('clicked()', self.onView32hr)
    

    self.renderRadioFrame = qt.QFrame(self.parent)
    self.renderRadioFrame.setLayout(qt.QVBoxLayout())
    self.radioButtonsFrame.layout().addWidget(self.renderRadioFrame)
    self.renderRadioLabel = qt.QLabel("Select volume to render: ", self.renderRadioFrame)
    self.renderRadioLabel.setToolTip( "Select Transaxial or Label volume")
    self.renderRadioFrame.layout().addWidget(self.renderRadioLabel)
    self.rThrshButton = qt.QRadioButton("Threshold", self.renderRadioFrame)
    self.rLabelButton = qt.QRadioButton("Label", self.renderRadioFrame)
    self.rThrshButton.checked = True
    self.renderRadioFrame.layout().addWidget(self.rThrshButton, 1, 0)
    self.renderRadioFrame.layout().addWidget(self.rLabelButton, 0, 0)
    self.rThrshButton.connect('clicked()', self.onThrshRender)
    self.rLabelButton.connect('clicked()', self.onLabelRender)

    #
    # the view selector
    #
    self.logic.setVolumeAttributes()
    self.logic.updateActiveVolumes()
    self.updateActiveViews()
    #self.viewSelectorFrame = qt.QFrame(self.parent)
    #self.viewSelectorFrame.setLayout(qt.QHBoxLayout())
    ##self.parent.layout().addWidget(self.viewSelectorFrame)
    #scrollingFormLayout.addWidget(self.viewSelectorFrame)

    #self.viewSelectorLabel = qt.QLabel("Select View: ", self.viewSelectorFrame)
    #self.viewSelectorLabel.setToolTip( "Select the 6, 24 or 32 Hour data set")
    #self.viewSelectorFrame.layout().addWidget(self.viewSelectorLabel)

    
    
    # Stats button
    self.statsButton = qt.QPushButton("Stats")
    self.statsButton.toolTip = "Calculate Statistics."
    self.statsButton.enabled = True
    #self.statsButton.name = "6HR"
    self.parent.layout().addWidget(self.statsButton)

    # model and view for stats table
    self.view = qt.QTableView()
    self.view.sortingEnabled = True
    self.parent.layout().addWidget(self.view)


    # Save button
    self.saveButton = qt.QPushButton("Save")
    self.saveButton.toolTip = "Calculate Statistics."
    self.saveButton.enabled = False
    self.parent.layout().addWidget(self.saveButton)

    # make connections
    self.statsButton.connect('clicked()', self.onStats)
    self.saveButton.connect('clicked()', self.onSave)
    self.refreshButton.connect('clicked()', self.onRefresh)
    self.slider.connect('valueChanged(double)', self.onSliderValueChanged)


    # call refresh the slider to set it's initial state
    self.onRefresh()

    # Add vertical spacer
    self.layout.addStretch(1)

  def getParameterNode(self):
    """Get the ColonicAnalysis parameter node - a singleton in the scene"""
    node = self._findParameterNodeInScene()
    if not node:
      node = self._createParameterNode()
    return node

  def _findParameterNodeInScene(self):
    node = None
    size =  slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLScriptedModuleNode")
    for i in xrange(size):
      n  = slicer.mrmlScene.GetNthNodeByClass( i, "vtkMRMLScriptedModuleNode" )
      if n.GetModuleName() == "ColonicAnalysis":
        node = n
    return node

  def _createParameterNode(self):
    """create the ColonicAnalysis parameter node - a singleton in the scene
    This is used internally by getParameterNode - shouldn't really
    be called for any other reason.
    """
    node = slicer.vtkMRMLScriptedModuleNode()
    node.SetSingletonTag( "ColonicAnalysis" )
    node.SetModuleName( "ColonicAnalysis" )
    node.SetParameter( "view", "6HRS" )
    slicer.mrmlScene.AddNode(node)
    # Since we are a singleton, the scene won't add our node into the scene,
    # but will instead insert a copy, so we find that and return it
    node = self._findParameterNodeInScene()
    return node

  # note: this method needs to be implemented exactly as-is
  # in each leaf subclass so that "self" in the observer
  # is of the correct type
  def updateParameterNode(self, caller, event):
    node = self.getParameterNode()
    if node != self.parameterNode:
      if self.parameterNode:
        node.RemoveObserver(self.parameterNodeTag)
      self.parameterNode = node
      self.parameterNodeTag = node.AddObserver(vtk.vtkCommand.ModifiedEvent, self.updateGUIFromMRML)

  def setMRMLDefaults(self):
    print("setMRMLDefaults()")
    disableState = self.parameterNode.GetDisableModifiedEvent()
    self.parameterNode.SetDisableModifiedEvent(1)
    defaults = (
      ("timepoints", "6HRS 24HRS 32HRS"),
      ("SummaryKeys", '"Label", "Voxels", "Volume cc", "Total Counts", "SPECT Mean"'),
      ("thresholds", '0 10 0'),
    )
    for d in defaults:
      param = "ColonicAnalysis,"+d[0]
      pvalue = self.parameterNode.GetParameter(param)
      if pvalue == '':
        self.parameterNode.SetParameter(param, d[1])
    self.parameterNode.SetDisableModifiedEvent(disableState)
    
  def updateGUIFromMRML(self,caller,event):
    print("updateGUIFromMRML()")
    params = ("timepoints", "thresholds",)
    for p in params:
      if self.parameterNode.GetParameter("ColonicAnalysis,"+p) == '':
        # don't update if the parameter node has not got all values yet
        return
    #self.disconnectWidgets()
    #self.toleranceSpinBox.setValue( float(self.parameterNode.GetParameter("WandEffect,tolerance")) )
    #self.maxPixelsSpinBox.setValue( float(self.parameterNode.GetParameter("WandEffect,maxPixels")) )
    #self.fillModeCheckBox.checked = self.parameterNode.GetParameter("WandEffect,fillMode") == "Volume"
    #self.toleranceFrame.setHidden( self.thresholdPaint.checked )
    #self.connectWidgets()


  def updateActiveViews(self):
    self.r6HRSButton.enabled = False
    self.r24HRSButton.enabled = False
    self.r32HRSButton.enabled = False
    for view in self.logic.getActiveSpects():
      if view == '6HRS':
        self.r6HRSButton.enabled = True
      if view == '24HRS':
        self.r24HRSButton.enabled = True
      if view == '32HRS':
        self.r32HRSButton.enabled = True
      

  def onFixvolumes(self):
    self.logic.fixVolumes()
    self.logic.setVolumeAttributes()
    self.logic.fixSpectLevel()
    self.changeView(self.logic.getCurrentView())
    self.fixvolumesButton.enabled = False
    self.updateActiveViews()

  def onRender(self):
    self.logic.renderView(self.logic.getCurrentView(), 'TH', 'threshold')
      
  def onView6hr(self):
    self.changeView("6HRS")
      
  def onView24hr(self):
    self.changeView("24HRS")
      
  def onView32hr(self):
    self.changeView("32HRS")

  def changeView(self, view):
    #print("changeView " + view)
    self.logic.setCurrentView(view)
    self.logic.setViews(view)
    #sThr, sMax = self.logic.getThreshold(self.logic.getCurrentView())
    self.slider.value = self.logic.getThreshold(view)
    self.slider.maximum = self.logic.getThresholdMax(view)
    self.clearStats()
    #if not self.logic.renderView('LA', 'label'):
    self.logic.renderView(self.logic.getCurrentView(), self.renderType[0], self.renderType[1])
    
  def onThrshRender(self):
    self.renderType = ('TH', 'threshold')
    
  def onLabelRender(self):
    self.renderType = ('LA', 'label')
    
  def onCalcThresholds(self):
    active = self.logic.getActiveSpects()
    for tp in active:
      sThr = self.logic.calculateThreshold(tp)
      self.logic.applyThreshold(tp, int(sThr))
    #sThr, sMax = self.logic.getThreshold(active[0])
    self.slider.maximum = self.logic.getThresholdMax(active[0])
    self.slider.value = self.logic.getThreshold(active[0])
    self.slider.enabled = True
    self.logic.setCurrentView(active[0])
    self.changeView(active[0])
    self.logic.updateActiveVolumes()
    self.thresholdButton.enabled = False
     
  def onSliderValueChanged(self,value):
    current = self.logic.getCurrentView()
    if self.logic.getThreshold(current) == 0 and value > 0:
      self.logic.applyThreshold(current, int(value))
      self.logic.updateActiveVolumes()
      self.changeView(current)

  def onTresholdRefresh(self):
      self.logic.applyThreshold(self.logic.getCurrentView(), self.slider.value)
      self.changeView(self.logic.getCurrentView())
      
      
  def onCreateLabels(self):
    active = self.logic.getActiveSpects()
    for tp in active:
      self.logic.setupPaint(tp)
    self.editorButton.enabled = False
     
  def onRefresh(self):
    volumeCount = self.logic.volumeCount()

  def volumesAreValid(self, timepoint):
    """Verify that the SPECT and label volumes exist for timepoint"""
    if self.logic.colonData[timepoint]['SP']['Active'] and self.logic.colonData[timepoint]['LA']['Active']:
      return True
    return False

  def onStats(self):
    """Calculate the label statistics
    """
    if not self.volumesAreValid(self.logic.getCurrentView()):
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Label Statistics", "Either the SPECT or Label volume does not exist.")
      return
    #self.statsButton.text = "Working..."
    # TODO: why doesn't processEvents alone make the label text change?
    self.statsButton.repaint()
    slicer.app.processEvents()
    #self.logic = ColonStatsLogic(self.grayscaleNode, self.labelNode)
    self.populateStats()
    #self.chartFrame.enabled = True
    self.saveButton.enabled = True
    self.statsButton.text = "Stats"

  def onSave(self):
    """save the label statistics
    """
    if not self.fileDialog:
      self.fileDialog = qt.QFileDialog(self.parent)
      self.fileDialog.options = self.fileDialog.DontUseNativeDialog
      self.fileDialog.acceptMode = self.fileDialog.AcceptSave
      self.fileDialog.defaultSuffix = "csv"
      self.fileDialog.setNameFilter("Comma Separated Values (*.csv)")
      self.fileDialog.connect("fileSelected(QString)", self.onFileSelected)
    self.fileDialog.show()

  def onFileSelected(self,fileName):
    self.logic.saveStats(fileName)

  def clearStats(self):
    self.items = []
    self.model = qt.QStandardItemModel()
    self.view.setModel(self.model)
    self.view.verticalHeader().visible = False
    
    
  def populateStats(self):
    if not self.logic:
      return
    labelvol = slicer.util.getNode(self.logic.colonData[self.logic.getCurrentView()]['LA']['ID'])
    #self.nodes = self.logic.getColonNodes(self.logic.getCurrentView())
    #labelvol = slicer.util.getNode(self.nodes['LABEL'])
    displayNode = labelvol.GetDisplayNode()
    colorNode = displayNode.GetColorNode()
    lut = colorNode.GetLookupTable()
    numLabels = colorNode.GetNumberOfColors()
    self.logic.computeMean(self.logic.getCurrentView())
    self.items = []
    self.model = qt.QStandardItemModel()
    self.view.setModel(self.model)
    self.view.verticalHeader().visible = False
    totalCounts = 0
    row = 0
    for i in self.logic.labelStats["Labels"]:
      color = qt.QColor()
      rgb = lut.GetTableValue(i)
      color.setRgb(rgb[0]*255,rgb[1]*255,rgb[2]*255)
      item = qt.QStandardItem()
      item.setData(color,1)
      item.setToolTip(colorNode.GetColorName(i))
      self.model.setItem(row,0,item)
      self.items.append(item)
      col = 1
      for k in self.logic.keys:
        item = qt.QStandardItem()
        item.setText(str(self.logic.labelStats[i,k]))
        item.setToolTip(colorNode.GetColorName(i))
        #print (colorNode.GetColorName(i))
        self.model.setItem(row,col,item)
        self.items.append(item)
        col += 1
      row += 1

    item = qt.QStandardItem()
    item.setText(str(self.logic.totalCounts))
    self.model.setItem(row,4,item)
    self.items.append(item)
    item = qt.QStandardItem()
    item.setText("%2.3f" % self.logic.computedMean)
    self.model.setItem(row,5,item)
    self.items.append(item)
    self.view.setColumnWidth(0,30)
    self.model.setHeaderData(0,1," ")
    col = 1
    for k in self.logic.keys:
      self.view.setColumnWidth(col,15*len(k))
      self.model.setHeaderData(col,1,k)
      col += 1


  def cleanup(self):
    pass


  def onReload(self,moduleName="ColonicAnalysis"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    import imp, sys, os, slicer

    widgetName = moduleName + "Widget"

    # reload the source code
    # - set source file path
    # - load the module to the global space
    filePath = eval('slicer.modules.%s.path' % moduleName.lower())
    p = os.path.dirname(filePath)
    if not sys.path.__contains__(p):
      sys.path.insert(0,p)
    fp = open(filePath, "r")
    globals()[moduleName] = imp.load_module(
        moduleName, fp, filePath, ('.py', 'r', imp.PY_SOURCE))
    fp.close()

    # rebuild the widget
    # - find and hide the existing widget
    # - create a new widget in the existing parent
    parent = slicer.util.findChildren(name='%s Reload' % moduleName)[0].parent().parent()
    for child in parent.children():
      try:
        child.hide()
      except AttributeError:
        pass
    # Remove spacer items
    item = parent.layout().itemAt(0)
    while item:
      parent.layout().removeItem(item)
      item = parent.layout().itemAt(0)

    # delete the old widget instance
    if hasattr(globals()['slicer'].modules, widgetName):
      getattr(globals()['slicer'].modules, widgetName).cleanup()

    # create new widget inside existing parent
    globals()[widgetName.lower()] = eval(
        'globals()["%s"].%s(parent)' % (moduleName, widgetName))
    globals()[widgetName.lower()].setup()
    setattr(globals()['slicer'].modules, widgetName, globals()[widgetName.lower()])

  def onReloadAndTest(self,moduleName="ColonicAnalysis"):
    try:
      self.onReload()
      evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
      tester = eval(evalString)
      tester.runTest()
    except Exception, e:
      import traceback
      traceback.print_exc()
      qt.QMessageBox.warning(slicer.util.mainWindow(), 
          "Reload and Test", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")


#
# ColonicAnalysisLogic
#

class ColonicAnalysisLogic:
    """This class should implement all the actual 
    computation done by your module.  The interface 
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget
    """
    def __init__(self):
        self.keys = ("Label", "Voxels", "Volume cc", "Total Counts", "SPECT Mean")
        self.colonRegions = ("precolon", "ascending_1", "ascending_2", "transverse_1", 
          "transverse_2", "transverse_3", "transverse_4", "neorectum", "stool")
        self.timepoints = ("6HRS", "24HRS", "32HRS")
        self.colonData = {
                      '6HRS': {'Name': '6HRS', 'Colour': 'Red', 'Threshold': {'val': 0, 'max': 0},
                            'CT': {'Active': False, 'Name': None, 'ID': None},
                            'SP': {'Active': False, 'Name': None, 'ID': None}, 
                            'TH': {'Active': False, 'Name': None, 'ID': None},
                            'LA': {'Active': False, 'Name': None, 'ID': None}},
                      '24HRS': {'Name': '24HRS', 'Colour': 'Green', 'Threshold': {'val': 0, 'max': 0},
                            'CT': {'Active': False, 'Name': None, 'ID': None},
                            'SP': {'Active': False, 'Name': None, 'ID': None}, 
                            'TH': {'Active': False, 'Name': None, 'ID': None},
                            'LA': {'Active': False, 'Name': None, 'ID': None}},
                      '32HRS': {'Name': '32HRS', 'Colour': 'Blue', 'Threshold': {'val': 0, 'max': 0},
                            'CT': {'Active': False, 'Name': None, 'ID': None},
                            'SP': {'Active': False, 'Name': None, 'ID': None}, 
                            'TH': {'Active': False, 'Name': None, 'ID': None},
                            'LA': {'Active': False, 'Name': None, 'ID': None}}}
        self.labelStats = {}
        self.labelStats['Labels'] = []
        self.totalCounts = 0
        self.currentView = self.timepoints[0]
        self.computedMean = 0.0
        self.volumesLogic = slicer.modules.volumes.logic()
        self.hasColourtable = False
        #self.modulePath = '/home/markp/Projects/slicer/ColonTools/ColonicAnalysis/'
        #self.modulePath = '/Volumes/Seagate Backup Plus Drive/Colonic/ColonTools/ColonicAnalysis/'
        modName = slicer.modules.colonicanalysis.path
        lsep = modName.rindex('/')
        self.modulePath = modName[0:lsep]
        pass

    def updateActiveVolumes(self):
      #print ("updateActiveVolumes()")
      for timePoint in self.colonData:
        nodes = slicer.util.getNodes('*%s*' % timePoint)
        for nodeName, nodeID in nodes.items():
            if nodeName.find("CTAC") != -1:
                self.colonData[timePoint]['CT']['Active'] = True
                self.colonData[timePoint]['CT']['Name'] = nodeName
                self.colonData[timePoint]['CT']['ID']= nodeID.GetID()
            if nodeName.endswith("Transaxials"):
                self.colonData[timePoint]['SP']['Active'] = True
                self.colonData[timePoint]['SP']['Name'] = nodeName
                self.colonData[timePoint]['SP']['ID']= nodeID.GetID()
            if nodeName.endswith("label"):
                self.colonData[timePoint]['LA']['Active'] = True
                self.colonData[timePoint]['LA']['Name'] = nodeName
                self.colonData[timePoint]['LA']['ID']= nodeID.GetID()
            if nodeName.endswith("Transaxials-threshold"):
                self.colonData[timePoint]['TH']['Active'] = True
                self.colonData[timePoint]['TH']['Name'] = nodeName
                self.colonData[timePoint]['TH']['ID']= nodeID.GetID()
        if not self.colonData[timePoint]['CT']['Active'] and (not self.colonData[timePoint]['SP']['Active'] and not self.colonData[timePoint]['TH']['Active']):
          print "%s: No CT or SPECT data" % timePoint
     
    def getActiveSpects(self):
      tPoints = []
      for tp in self.timepoints:
        if self.colonData[tp]['SP']['Active']:
          tPoints.append(tp)
      return tPoints

    def getViews(self):
      return self.timepoints
      
    def getCurrentView(self):
      return self.currentView
      
    def setCurrentView(self, view):
      self.currentView = view
      
    def fixVolumes(self):
      """ The current DICOM import does not load the z spacing correctly for SPECT images.
          This function copies x size to z size and also corrects an orientation issue.
      """
      self.updateActiveVolumes()
      self.labelStats = {}
      self.labelStats['Labels'] = []
      self.totalCounts = 0
      self.currentView = self.getActiveSpects()[0]
      self.computedMean = 0.0
      layoutManager = slicer.app.layoutManager()
      for timePoint in self.colonData:
        if self.colonData[timePoint]['SP']['Active']:
          volumeNode = slicer.util.getNode(self.colonData[timePoint]['SP']['ID'])
          mymat = vtk.vtkMatrix4x4()
          (sx,sy,sz) = volumeNode.GetSpacing()
          sz = sx
          volumeNode.SetSpacing(sx,sy,sz)
          volumeNode.GetIJKToRASDirectionMatrix(mymat)
          mymat.SetElement(2,2,-1.0)
          volumeNode.SetIJKToRASDirectionMatrix(mymat)
          self.volumesLogic.CenterVolume(volumeNode)
      self.setSpectColours()
      self.setCTWindow()
      layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)     


    def setSpectColours(self):
      """ Set a different colour for each SPECT timpoint
      """
      for timePoint in self.colonData:
        if self.colonData[timePoint]['SP']['Active']:
          volumeNode = slicer.util.getNode(self.colonData[timePoint]['SP']['ID'])
          displayNode = volumeNode.GetDisplayNode()
          displayNode.SetAndObserveColorNodeID("vtkMRMLColorTableNode"+self.colonData[timePoint]['Colour'])

    def setCTWindow(self):
      """ Set CT windowing for the colon.
      """
      for timePoint in self.colonData:
        if self.colonData[timePoint]['CT']['Active']:
          volumeNode = slicer.util.getNode(self.colonData[timePoint]['CT']['ID'])
          displayNode = volumeNode.GetDisplayNode()
          displayNode.SetAutoWindowLevel(0)
          displayNode.SetWindowLevel(350.0, 40.0)
      
        
    def fixSpectLevel(self):
      """ The auto level is incorrectly set to a very small valuefor some SPECT volumes.
          If the level is below 1/3 the window width, set it to 1/2 window width.
      """
      for timePoint in self.colonData:
        if self.colonData[timePoint]['SP']['Active']:
          volumeNode = slicer.util.getNode(self.colonData[timePoint]['SP']['ID'])
          displayNode = volumeNode.GetDisplayNode()
          window = displayNode.GetWindow()
          level =  displayNode.GetLevel()
          if window < 50:
            window = window * 10.0
            displayNode.SetAutoWindowLevel(0)
            displayNode.SetWindow(window)
          if level < (window/3.0):
            print "Adjust Window Level"
            displayNode.SetAutoWindowLevel(0)
            displayNode.SetLevel(window/2.0)
        
     
    def setVolumeAttributes(self):
      nodes = slicer.util.getNodes('*HR*')
      for nodeName, nodeID in nodes.items():
        if nodeName.find("CTAC") != -1:
          nodeID.SetAttribute("CT", "1")
          nodeID.SetAttribute("SelectView", "0")
        elif nodeName.endswith("Transaxials"):
          nodeID.SetAttribute("SelectView", "1")
        elif nodeName.endswith("label"):
          nodeID.SetAttribute("SelectView", "0")
        elif nodeName.endswith("threshold"):
          nodeID.SetAttribute("SelectView", "0")
        else:
          nodeID.SetAttribute("SelectView", "0")
      
    def view6hr(self):
        appLogic = slicer.app.applicationLogic()
        selectionNode = appLogic.GetSelectionNode()
        sVolumeNode = slicer.util.getNode(pattern="*6*EM*")
        cVolumeNode = slicer.util.getNode(pattern="*CT*6*")
        if cVolumeNode == None:
            selectionNode.SetReferenceActiveVolumeID(sVolumeNode.GetID())
            for sliceCompositeNode in slicer.util.getNodes('vtkMRMLSliceCompositeNode*').values():
                sliceCompositeNode.SetForegroundOpacity(0.0)
                sliceCompositeNode.SetLinkedControl(1)
        else:
            selectionNode.SetReferenceActiveVolumeID(cVolumeNode.GetID())
            selectionNode.SetReferenceSecondaryVolumeID(sVolumeNode.GetID())
            for sliceCompositeNode in slicer.util.getNodes('vtkMRMLSliceCompositeNode*').values():
                sliceCompositeNode.SetForegroundOpacity(0.5)
                sliceCompositeNode.SetLinkedControl(1)
        appLogic.PropagateVolumeSelection()

        
    def setViews(self, timePoint):
      """ Set the CT, SPECT and Label volumes in R,Y,G views for timePoint.
          If CT is not available set SPECT as background.
      """
      #print ("setViews() " + timePoint)
      setActive = False
      setSecondary = False
      setLabel = False
      self.labelStats = {}
      self.labelStats['Labels'] = []
      self.totalCounts = 0
      self.computedMean = 0.0
      appLogic = slicer.app.applicationLogic()
      selectionNode = appLogic.GetSelectionNode()
      selectionNode.SetReferenceActiveVolumeID(None)
      selectionNode.SetReferenceSecondaryVolumeID(None)
      selectionNode.SetReferenceActiveLabelVolumeID(None)
      appLogic.PropagateVolumeSelection()
      cdt = self.colonData[timePoint]
      if cdt['CT']['Active']:
        selectionNode.SetReferenceActiveVolumeID(cdt['CT']['ID'])
        if cdt['TH']['Active']:
          selectionNode.SetReferenceSecondaryVolumeID(cdt['TH']['ID'])
        else:
          selectionNode.SetReferenceSecondaryVolumeID(cdt['SP']['ID'])
        for sliceCompositeNode in slicer.util.getNodes('vtkMRMLSliceCompositeNode*').values():
            sliceCompositeNode.SetForegroundOpacity(0.5)
            sliceCompositeNode.SetLinkedControl(1)
      else:
        if cdt['TH']['Active']:
          selectionNode.SetReferenceActiveVolumeID(cdt['TH']['ID'])    
        else:
          selectionNode.SetReferenceSecondaryVolumeID(cdt['SP']['ID'])
      if not cdt['LA']['Active']:
          selectionNode.SetReferenceActiveLabelVolumeID(cdt['LA']['ID'])
      appLogic.PropagateVolumeSelection()
     
     
    def renderView(self, timePoint, vtype, vend):
      #print ("renderView " + vtype)
      if not self.colonData[timePoint][vtype]['Active']:
        return False
      volumesLogic = slicer.modules.volumes.logic()
      volumerenderlogic = slicer.modules.volumerendering.logic()
      foundNode = False
      #displayNode = None
      displayNode = slicer.util.getNode('%s VolumeRendering-%s' % (timePoint, vend))
      if displayNode == None:
        print "Create new node"
        volumeNode = slicer.util.getNode(self.colonData[timePoint][vtype]['ID'])
        displayNode = volumerenderlogic.CreateVolumeRenderingDisplayNode()
        node = slicer.mrmlScene.AddNode(displayNode)
        node.SetName('%s VolumeRendering-%s' % (timePoint, vend))
        displayNode.UnRegister(volumerenderlogic)
        volumerenderlogic.UpdateDisplayNodeFromVolumeNode(displayNode, volumeNode)
        node.GetVolumePropertyNode().SetName('%s VolumeProperty-%s' % (timePoint, vend))
        node.GetROINode().SetName('%s AnnotationROI-%s' % (timePoint, vend))
        volumeNode.AddAndObserveDisplayNodeID(displayNode.GetID())
      else:
        volumeNode = slicer.util.getNode(displayNode.GetVolumeNodeID())
        volumeName = volumeNode.GetName()
        propertyNode = slicer.util.getNode('%s VolumeProperty-%s' % (timePoint, vend))
        annotationNode = slicer.util.getNode('AnnotationROI')
        volumerenderlogic.CopyDisplayToVolumeRenderingDisplayNode(displayNode, volumeNode.GetDisplayNode())
      displayNode.GetVolumePropertyNode().GetVolumeProperty().ShadeOff()
      return True
        
      
    def getColonNodes(self, timePoint):
        colonNodes = dict(CT=None, SPECT=None, LABEL=None, THRESHOLD=None)
        nodes = slicer.util.getNodes('*%s*' % timePoint)
        for nodeName, nodeID in nodes.items():
            if nodeName.find("CTAC") != -1:
                colonNodes['CT'] = nodeID.GetID()
            if nodeName.endswith("Transaxials"):
                colonNodes['SPECT'] = nodeID.GetID()
            if nodeName.endswith("label"):
                colonNodes['LABEL'] = nodeID.GetID()
            if nodeName.endswith("threshold"):
                colonNodes['THRESHOLD'] = nodeID.GetID()
        if colonNodes['CT'] == None and (colonNodes['SPECT'] == None and colonNodes['THRESHOLD'] == None):
            print "No CT or SPECT data!"
        return colonNodes
        

    def calculateThreshold(self, timePoint):
      """ Calculate a threshold value to remove background from SPECT.
      """
      print "calculateThreshold(%s)" % timePoint
      cvt = self.colonData[timePoint]
      arrayv = slicer.util.array(cvt['SP']['ID'])
      volumeNode = slicer.util.getNode(cvt['SP']['ID'])
      cvt['Threshold']['max'] = arrayv.max()
      myVals, myLimits = np.histogram(arrayv, bins = 100)
      cvt['Threshold']['val'] = myLimits[9]
      print("%d, %d" % (cvt['Threshold']['val'], cvt['Threshold']['max']))
      volName = cvt['SP']['Name']
      if cvt['TH']['Active']:
        outputVolume = slicer.util.getNode(cvt['TH']['ID'])
      else:
        outputVolume = self.volumesLogic.CloneVolume(slicer.mrmlScene, volumeNode, volName+'-threshold')
        self.updateActiveVolumes()
      return cvt['Threshold']['val']
        
    def applyThreshold(self, timePoint, thrsh):
        #print "applyThreshold(%s)" % timePoint
        if not self.colonData[timePoint]['TH']['Active']:
          return
        parameters = {}
        self.colonData[timePoint]['Threshold']['val'] = thrsh
        volumeNode = slicer.util.getNode(self.colonData[timePoint]['SP']['ID'])
        outputVolume = slicer.util.getNode(self.colonData[timePoint]['TH']['ID'])
        if not (volumeNode and outputVolume):
            qt.QMessageBox.critical(
                slicer.util.mainWindow(),
                'Threshold', 'You must run Calculate Threshold first')
            return
        #print outputVolume.GetName()
        parameters['InputVolume'] = volumeNode
        parameters['OutputVolume'] = outputVolume
        parameters['ThresholdValue'] = thrsh
        parameters['ThresholdType'] = 'Below'
        slicer.cli.run(slicer.modules.thresholdscalarvolume, None, parameters, wait_for_completion=True)
        return
        
    def getThreshold(self, timepoint):
      return self.colonData[timepoint]['Threshold']['val']
      
    def getThresholdMax(self, timepoint):
      return self.colonData[timepoint]['Threshold']['max']
      
      
    def volumeCount(self):
        return len(slicer.util.getNodes('vtkMRML*VolumeNode*'))

    def selectVolume(self,index):
      nodes = slicer.util.getNodes('vtkMRML*VolumeNode*')
      names = nodes.keys()
      names.sort()
      selectionNode = slicer.app.applicationLogic().GetSelectionNode()
      selectionNode.SetReferenceActiveVolumeID( nodes[names[index]].GetID() )
      slicer.app.applicationLogic().PropagateVolumeSelection(0)
        
    def computeMean(self, timePoint):
      import numpy.ma as ma
      cvt = self.colonData[self.currentView]
      arrayv = slicer.util.array(cvt['SP']['ID'])
      arrayl = slicer.util.array(cvt['LA']['ID'])
      cubicMMPerVoxel = reduce(lambda x,y: x*y, slicer.util.getNode(cvt['SP']['ID']).GetSpacing())
      #arrayv = slicer.util.array(nodes['SPECT'])
      #arrayl = slicer.util.array(nodes['LABEL'])
      #cubicMMPerVoxel = reduce(lambda x,y: x*y, slicer.util.getNode(nodes['LABEL']).GetSpacing())
      ccPerCubicMM = 0.001
      #ma.masked_array(arrayv, (arrayl != 2)).sum()
      #totalCounts = 0
      roiCounts = [0]
      for i in range(1,len(self.colonRegions)):
          self.labelStats["Labels"].append(i)
          self.labelStats[i,"Label"] = i
          self.labelStats[i,"Voxels"] = 0
          self.labelStats[i,"Total Counts"] = 0
          if (arrayl == i).any():
              maskedArray = ma.masked_array(arrayv, (arrayl != i))
              self.labelStats[i,"Voxels"] = (maskedArray > 0).sum()
              myCounts = maskedArray.sum()
              self.labelStats[i,"Total Counts"] = myCounts
              roiCounts.append(myCounts)
              self.totalCounts += myCounts
          else:
              roiCounts.append(0)
          self.labelStats[i,"Volume cc"] = "%2.3f" % (self.labelStats[i,"Voxels"] * cubicMMPerVoxel * ccPerCubicMM)
      #computedMean = 0.0
      for i in range(len(roiCounts)):
          sm = 0;
          if self.totalCounts:
            sm = (float(roiCounts[i])/float(self.totalCounts))*float(i)
          self.labelStats[i,"SPECT Mean"] = "%2.3f" % sm
          self.computedMean += sm
        
    def statsAsCSV(self):
      """
      print comma separated value file with header keys in quotes
      """
      csv = ""
      header = ""
      for k in self.keys[:-1]:
        header += "\"%s\"" % k + ","
      header += "\"%s\"" % self.keys[-1] + "\n"
      csv = header
      for i in self.labelStats["Labels"]:
        line = ""
        for k in self.keys[:-1]:
          line += str(self.labelStats[i,k]) + ","
        line += str(self.labelStats[i,self.keys[-1]]) + "\n"
        csv += line
      return csv

    def saveStats(self,fileName):
      fp = open(fileName, "w")
      fp.write(self.statsAsCSV())
      fp.close()
      
    def setupPaint(self, timePoint):
      print ("setupPaint()")
      if not self.hasColourtable:
        self.hasColourtable = slicer.util.loadColorTable(self.modulePath+'/ColonColors.txt')
        if not self.hasColourtable:
          print "Error: THe Colon Colour table has not loaded"
          return
      if self.colonData[timePoint]['LA']['Active']:
        return
      applicationLogic = slicer.app.applicationLogic()
      volumesLogic = slicer.modules.volumes.logic()
      colorLogic = slicer.modules.colors.logic()
      if self.colonData[timePoint]['TH']['Active']:
        volumeNode = slicer.util.getNode(self.colonData[timePoint]['TH']['ID'])
        labelNode = volumesLogic.CreateAndAddLabelVolume(volumeNode, volumeNode.GetName()+'-label')
        labelNode.GetDisplayNode().SetAndObserveColorNodeID('vtkMRMLColorTableNodeFileColonColors.txt')
        self.updateActiveVolumes()

    
class ColonicAnalysisTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_ColonicAnalysis1()

  def test_ColonicAnalysis1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests sould exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        print('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        print('Loading %s...\n' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading\n')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = ColonicAnalysisLogic()
    volumesLogic = slicer.modules.volumes.logic()

    blurLevelCount = 10
    for sigma in range(blurLevelCount):
      self.delayDisplay('Making blurred volume with sigma of %d\n' % sigma)
      outputVolume = volumesLogic.CloneVolume(slicer.mrmlScene, volumeNode, 'blur-%d' % sigma)
      parameters = {
          "inputVolume": slicer.util.getNode('FA'),
          "outputVolume": outputVolume,
          "sigma": sigma,
          }

      blur = slicer.modules.gaussianblurimagefilter
      slicer.cli.run(blur, None, parameters, wait_for_completion=True)

    slicer.modules.ColonicAnalysisWidget.onRefresh()
    self.delayDisplay('Selecting original volume')
    slicer.modules.ColonicAnalysisWidget.slider.value = 0
    self.delayDisplay('Selecting final volume')
    slicer.modules.ColonicAnalysisWidget.slider.value = blurLevelCount

    selectionNode = slicer.app.applicationLogic().GetSelectionNode()
    selectedID = selectionNode.GetActiveVolumeID()
    lastVolumeID = outputVolume.GetID()
    if selectedID != lastVolumeID:
      raise Exception("Volume ID was not selected!\nExpected %s but got %s" % (lastVolumeID, selectedID))

    self.delayDisplay('Test passed!')
