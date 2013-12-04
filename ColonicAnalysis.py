import os
import unittest
from __main__ import vtk, qt, ctk, slicer
import numpy as np
import numpy.ma as ma

#
# ColonicAnalysis
#

class ColonicAnalysis:
  def __init__(self, parent):
    parent.title = "ColonicAnalysis" # TODO make this more human readable by adding spaces
    parent.categories = ["Examples"]
    parent.dependencies = []
    parent.contributors = ["Jean-Christophe Fillion-Robin (Kitware), Steve Pieper (Isomics)"] # replace with "Firstname Lastname (Org)"
    parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    """
    parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc. and Steve Pieper, Isomics, Inc.  and was partially funded by NIH grant 3P41RR013218-12S1.
    Modified for Colonic Transit Analysis by Mark Pearson.
""" # replace with organization, grant and thanks.
    self.parent = parent

    parent.icon = qt.QIcon("/home/markp/Projects/slicer/ColonTools/ColonicAnalysis/Resources/Icons/Colon128.png")
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

class ColonicAnalysisWidget:
  def __init__(self, parent = None):
    self.chartOptions = ("Count", "Total", "Volume cc", "Min", "Max", "Mean")
    self.fileName = None
    self.fileDialog = None
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

    self.viewRadioFrame = qt.QFrame(self.parent)
    self.viewRadioFrame.setLayout(qt.QVBoxLayout())
    scrollingFormLayout.addWidget(self.viewRadioFrame)
    
    self.viewRadioLabel = qt.QLabel("Select View: ", self.viewRadioFrame)
    self.viewRadioLabel.setToolTip( "Select the 6, 24 or 32 Hour data set")
    self.viewRadioFrame.layout().addWidget(self.viewRadioLabel)

    #self.radioSubFrame = qt.QFrame(self.viewRadioFrame)
    #self.selectLayout = qt.QGridLayout()
    #self.radioSubFrame.setLayout(self.selectLayout)
    self.r6Button = qt.QRadioButton("6 Hours", self.viewRadioFrame)
    self.r24Button = qt.QRadioButton("24 Hours", self.viewRadioFrame)
    self.r32Button = qt.QRadioButton("32 Hours", self.viewRadioFrame)
    self.r6Button.checked = True
    self.viewRadioFrame.layout().addWidget(self.r6Button, 1, 0)
    self.viewRadioFrame.layout().addWidget(self.r24Button, 0, 0)
    self.viewRadioFrame.layout().addWidget(self.r32Button, 0, 0)
    

    #
    # the view selector
    #
    self.logic.setVolumeAttributes()
    self.logic.updateActiveVolumes()
    #self.viewSelectorFrame = qt.QFrame(self.parent)
    #self.viewSelectorFrame.setLayout(qt.QHBoxLayout())
    ##self.parent.layout().addWidget(self.viewSelectorFrame)
    #scrollingFormLayout.addWidget(self.viewSelectorFrame)

    #self.viewSelectorLabel = qt.QLabel("Select View: ", self.viewSelectorFrame)
    #self.viewSelectorLabel.setToolTip( "Select the 6, 24 or 32 Hour data set")
    #self.viewSelectorFrame.layout().addWidget(self.viewSelectorLabel)

    
    
    self.renderButton = qt.QPushButton("Render")
    scrollingFormLayout.addRow(self.renderButton)
    #self.view24hrButton = qt.QPushButton("View 24HR Volumes")
    #scrollingFormLayout.addRow(self.view24hrButton)
    #self.view32hrButton = qt.QPushButton("View 32HR Volumes")
    #scrollingFormLayout.addRow(self.view32hrButton)

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
    self.renderButton.connect('clicked()', self.onRender)
    #self.view24hrButton.connect('clicked()', self.onView24hr)
    #self.view32hrButton.connect('clicked()', self.onView32hr)
    self.r6Button.connect('clicked()', self.onView6hr)
    self.r24Button.connect('clicked()', self.onView24hr)
    self.r32Button.connect('clicked()', self.onView32hr)
    self.statsButton.connect('clicked()', self.onStats)
    self.saveButton.connect('clicked()', self.onSave)
    self.refreshButton.connect('clicked()', self.onRefresh)
    self.slider.connect('valueChanged(double)', self.onSliderValueChanged)
    #self.viewSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onViewSelect)


    # call refresh the slider to set it's initial state
    self.onRefresh()

    # Add vertical spacer
    self.layout.addStretch(1)

  #def onSliderValueChanged(self,value):
    #self.logic.selectVolume(int(value))

  def onFixvolumes(self):
    self.logic.fixVolumes()
    nodes = self.logic.getColonNodes("32HR")
    if nodes['SPECT'] == None:
        self.r32Button.enabled = False
    else:
        self.r32Button.enabled = True
    self.logic.setVolumeAttributes()
    self.logic.fixSpectLevel()
    self.changeView(self.logic.currentView)
    
  def onRender(self):
    self.logic.renderView(self.logic.currentView, 'TH', 'threshold')
      
  def onView6hr(self):
    self.changeView("6HRS")
      
  def onView24hr(self):
    self.changeView("24HRS")
      
  def onView32hr(self):
    self.changeView("32HRS")

  def changeView(self, view):
    #print("changeView " + view)
    self.logic.currentView = view
    self.logic.setViews(self.logic.currentView)
    sMax, sThr = self.logic.getThreshold(self.logic.currentView)
    self.slider.value = sThr
    self.slider.maximum = sMax
    self.clearStats()
    #if not self.logic.renderView('LA', 'label'):
    self.logic.renderView(self.logic.currentView, 'TH', 'threshold')
    
  def onViewSelect(self, node):
    print ("onViewSelect")
    if node == None:
      return
    name = node.GetName()
    if name.find("6HRS") != -1:
      self.changeView("6HRS")
    if name.find("24HRS") != -1:
      self.changeView("24HRS")
    if name.find("32HRS") != -1:
      self.changeView("32HRS")

    
  #def onCalcThreshold(self):
    #sMax, sThr = self.logic.calculateThreshold(self.logic.currentView)
    #self.slider.maximum = sMax
    #self.slider.value = sThr
    #self.slider.enabled = True
    #self.changeView(self.logic.currentView)
    #self.logic.updateActiveVolumes()
     
  def onCalcThresholds(self):
    active = self.logic.getActiveSpects()
    for tp in active:
      sThr = self.logic.calculateThreshold(tp)
      self.logic.applyThreshold(tp, int(sThr))
    sMax, sThr = self.logic.getThreshold(active[0])
    self.slider.maximum = sMax
    self.slider.value = sThr
    self.slider.enabled = True
    self.changeView(active[0])
    self.logic.currentView = active[0]
    self.logic.updateActiveVolumes()
     
  def onSliderValueChanged(self,value):
      if self.logic.colonData[self.logic.currentView]['Threshold']['val'] == 0 and value > 0:
        self.logic.applyThreshold(self.logic.currentView, int(value))
        self.logic.updateActiveVolumes()
        self.changeView(self.logic.currentView)

  def onTresholdRefresh(self):
      self.logic.applyThreshold(self.logic.currentView, self.slider.value)
      self.changeView(self.logic.currentView)
      
      
  def onCreateLabels(self):
    active = self.logic.getActiveSpects()
    for tp in active:
      self.logic.setupPaint(tp)
     
  def onRefresh(self):
    volumeCount = self.logic.volumeCount()
    #self.slider.enabled = volumeCount > 0
    #self.slider.maximum = volumeCount-1

  def volumesAreValid(self, timepoint):
    """Verify that the SPECT and label volumes exist for timepoint"""
    if self.logic.colonData[timepoint]['SP']['Active'] and self.logic.colonData[timepoint]['LA']['Active']:
      return True
    return False

  def onStats(self):
    """Calculate the label statistics
    """
    if not self.volumesAreValid(self.logic.currentView):
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
    labelvol = slicer.util.getNode(self.logic.colonData[self.logic.currentView]['LA']['ID'])
    #self.nodes = self.logic.getColonNodes(self.logic.currentView)
    #labelvol = slicer.util.getNode(self.nodes['LABEL'])
    displayNode = labelvol.GetDisplayNode()
    colorNode = displayNode.GetColorNode()
    lut = colorNode.GetLookupTable()
    numLabels = colorNode.GetNumberOfColors()
    self.logic.computeMean(self.logic.currentView)
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
        self.thresholds = {'6HR': 0, '24HR': 0, '32HR': 0}
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
        self.modulePath = '/home/markp/Projects/slicer/ColonTools/ColonicAnalysis/'
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
      
    def fixVolumes(self):
      """ The current DICOM import does not load the z spacing correctly for SPECT images.
          This function copies x size to z size and also corrects an orientation issue.
      """
      self.updateActiveVolumes()
      self.labelStats = {}
      self.labelStats['Labels'] = []
      self.totalCounts = 0
      self.currentView = self.timepoints[0]
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
      return [self.colonData[timepoint]['Threshold']['max'], self.colonData[timepoint]['Threshold']['val']]
      
      
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
      #print ("setupPaint()")
      if not self.hasColourtable:
        self.hasColourtable = slicer.util.loadColorTable(self.modulePath+'ColonColors.txt')
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
