import maya.cmds as cmds
import maya.OpenMaya as api
import maya.OpenMayaUI as apiUI
from xml.dom import minidom
from functools import partial
import os as os
import datetime
import shutil
import maya.mel as mel

class UI():
	'''
	gf_playblastManager User Interface class
	'''
	def __init__(self):
		self.fileLocation = os.path.split(__file__)[0] + "/"						# script path
		self.location = {}															# path list
		
		self.version = "1.1.0"					# script version
		
		try:									# current user
			self.user = os.getenv('USERNAME')
		except:
			self.user = "UNKNOWN"
		
		# write option file		
		if not os.path.exists(self.fileLocation + "gf_playblastManager_options.xml"):
			doc = minidom.Document()
			rootNode = doc.createElement("OPTIONS")
			doc.appendChild(rootNode)
			rootNode.setAttribute( "version", self.version )
			
			initDir = cmds.fileDialog2(fm=3, caption = "Choose a directory...", okc="OK")[0]
			
			result = cmds.promptDialog(
                title='Project Name',
                message='Enter Name:',
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')
			if result == 'OK':
				text = cmds.promptDialog(query=True, text=True)
			if result == 'Cancel':
				text = "default"
			
			directories = doc.createElement("directories")
			rootNode.appendChild(directories)
			default = doc.createElement("dir")
			directories.appendChild(default)
			default.setAttribute("path", initDir)
			default.setAttribute("name", text)
			
			defDir = doc.createElement("defDir")
			directories.appendChild(defDir)
			defDir.setAttribute("path", initDir)
			defDir.setAttribute("name", text)
			
			optionsFile = open(self.fileLocation + "gf_playblastManager_options.xml", "w")
			optionsFile.write(doc.toprettyxml())
			optionsFile.close()
			print "options initialised"
			
			# option var
			cmds.optionVar(iv=["PBMSeq",0])
			cmds.optionVar(iv=["PBMScene",0])
			cmds.optionVar(iv=["PBMShot",1])
			
			
		# read options
		
		optFile = minidom.parse(self.fileLocation + "gf_playblastManager_options.xml")										# parse options
		
		for obj in optFile.getElementsByTagName("dir"):																		# add extra directories to the location list
			path = obj.attributes["path"].value
			name = obj.attributes["name"].value
			self.location[name] = {}
			self.location[name]["path"] = path
		
		self.currentPath = optFile.getElementsByTagName("defDir")[0].attributes["path"].value								# current directory
		self.currentProject = optFile.getElementsByTagName("defDir")[0].attributes["name"].value							# current directory
		
		# initialize folders
		for loc in self.location.keys():
			if not os.path.exists(self.location[loc]["path"] + "/archive/"):																# archives folder
				os.makedirs(self.location[loc]["path"] + "/archive/")
				
		# initialize project registry
			if not os.path.exists(self.location[loc]["path"] + "/registry.xml"):
				doc = minidom.Document()
				rootNode = doc.createElement("REGISTRY")
				doc.appendChild(rootNode)
				
				registerFile = open(self.location[loc]["path"] + "/registry.xml", "w")
				registerFile.write(doc.toprettyxml())
				registerFile.close()
				
	def main(self):
		self.title = "GF Playblast Manager " + self.version
		
		# check main window existence
		if cmds.window("GF_PBM_MAIN_WIN",query=True,exists=True):
			cmds.deleteUI("GF_PBM_MAIN_WIN")
		
		# build main window
		self.mainWin = cmds.window("GF_PBM_MAIN_WIN", title=self.title)
		self.mainCol = cmds.columnLayout(rs = 2, co=("both",15))
		
		
		# path menu
		self.pathOpm = cmds.optionMenu(w = 200, h = 20, label = "Current Project : ", parent = self.mainCol, cc=self.changeProj)																			# Current Path optionMenu
		cmds.separator(h = 5,style="single",w=400)
		
		
		# main tab
		self.mainTab = cmds.tabLayout(w=400,h=620,parent = self.mainCol)
		self.readScroll = cmds.scrollLayout(parent = self.mainTab)
		self.writeScroll = cmds.scrollLayout(parent = self.mainTab)
		self.optionsScroll = cmds.scrollLayout(parent = self.mainTab)
		cmds.tabLayout(self.mainTab,edit=True,tabLabel=([self.readScroll,"Playblasts"],[self.writeScroll,"Add New"],[self.optionsScroll,"Options"]))
		
		cmds.showWindow(self.mainWin)
		cmds.window(self.mainWin, edit=True, wh = (434,665))
		self.loadTabs()
		self.loadReadTab()
	
	def changeProj(self,*args):
		self.currentProject = cmds.optionMenu(self.pathOpm,q=True,v=True)
		self.currentPath = self.location[self.currentProject]["path"]
		self.loadTabs()
		self.loadReadTab()
	
	def loadTabs(self):
		if cmds.optionMenu(self.pathOpm,q=True,ils=True) is not None:
			cmds.deleteUI(cmds.optionMenu(self.pathOpm,q=True,ils=True))
		for loc in self.location.keys():
			cmds.menuItem(label = loc, parent = self.pathOpm)
		
		cmds.optionMenu(self.pathOpm,e=True,v=self.currentProject)
		
		
		
		# load write tab
		#		 delete children
		if cmds.layout(self.writeScroll,q=True,nch=True) > 0:
			for obj in cmds.layout(self.writeScroll, q=True, childArray = True):
				cmds.deleteUI(obj)
		
		self.writeLayout = cmds.columnLayout(rs = 4, parent = self.writeScroll)
		cmds.separator(style="in",h=2,w=275, parent = self.writeLayout)
		cmds.rowLayout(nc=4,cw=([1,65],[2,50],[3,50],[4,50]), parent = self.writeLayout)
		cmds.text(label = " Project Name")
		cmds.text(label = " Seq.")
		cmds.text(label = " Scene")
		cmds.text(label = " Shot")
		cmds.rowLayout(nc=4,cw=([1,65],[2,50],[3,50],[4,50]), parent = self.writeLayout)
		self.projectTxf = cmds.textField(w=65,text = self.currentProject)
		self.seqField = cmds.intField(w = 50, value = cmds.optionVar(q="PBMSeqValue"))
		self.sceneField = cmds.intField(w = 50, value = cmds.optionVar(q="PBMSceneValue"))
		self.shotField = cmds.intField(w = 50, value = cmds.optionVar(q="PBMShotValue"))
		cmds.rowLayout(nc=4,cw=([1,65],[2,50],[3,50],[4,50]),cl4=["left","right","right","right"], parent = self.writeLayout)
		cmds.text(label = " Enable :")
		self.seqCbx = cmds.checkBox(label = "", value = cmds.optionVar(q="PBMSeq"),cc=self.grammarSwitch)
		self.sceneCbx = cmds.checkBox(label = "", value = cmds.optionVar(q="PBMScene"),cc=self.grammarSwitch)
		self.shotCbx = cmds.checkBox(label = "", value = cmds.optionVar(q="PBMShot"),cc=self.grammarSwitch)
		self.userTxf = cmds.textFieldGrp(label="User :", w=250,cw=([1,65],[2,65]),cal=([1,"left"],[2,"left"]), parent = self.writeLayout, text=self.user)
		cmds.separator(style="in",h=2,w=275, parent = self.writeLayout)
		self.viewCbx = cmds.checkBox(label = "View", value = cmds.optionVar(q="playblastViewerOn"), parent = self.writeLayout)
		self.ornamentsCbx = cmds.checkBox(label = "Show Ornaments", value = cmds.optionVar(q="playblastShowOrnaments"), parent = self.writeLayout)
		self.offscreenCbx = cmds.checkBox(label = "Render Offscreen", value = cmds.optionVar(q="playblastOffscreen"), parent = self.writeLayout)
		self.multicamCbx = cmds.checkBox(label = "Multi Camera Output", value = cmds.optionVar(q="playblastMultiCamera"), parent = self.writeLayout)
		cmds.separator(style="in",h=2,w=275, parent = self.writeLayout)
		self.formatOpt = cmds.optionMenuGrp(label="Format :  ",w=250,cw=([1,65],[2,150]),cal=([1,"left"],[2,"left"]), parent = self.writeLayout, cc=self.encodingList)
		cmds.menuItem(label = "avi")
		cmds.menuItem(label = "qt")
		cmds.menuItem(label = "image")
		self.encodeOpt = cmds.optionMenuGrp(label="Encoding :  ", w=250,cw=([1,65],[2,150]),cal=([1,"left"],[2,"left"]), parent = self.writeLayout)
		cmds.optionMenuGrp(self.formatOpt,edit=True,v=cmds.optionVar(q="playblastFormat"))
		self.encodingList()
		cmds.optionMenuGrp(self.encodeOpt,edit=True,v=cmds.optionVar(q="playblastCompression"))
		self.qualitySlider = cmds.intSliderGrp(label="Quality :  ", w=250,cw=([1,65],[2,35],[3,140]),cal=([1,"left"],[2,"left"]),field=True,value = cmds.optionVar(q="playblastQuality"),min=0,max=100, parent = self.writeLayout)
		cmds.separator(style="in",h=2,w=275, parent = self.writeLayout)
		self.displayOpt = cmds.optionMenuGrp(label="Size :  ",w=250,cw=([1,65],[2,150]),cal=([1,"left"],[2,"left"]), parent = self.writeLayout, cc=self.sizeModeSwitch)
		cmds.menuItem(label = "From Window")
		cmds.menuItem(label = "Custom")
		self.displayField = cmds.intFieldGrp( numberOfFields=2, label = '', cw=([1,65],[2,75],[3,75]), value1=cmds.optionVar(q="playblastWidth"), value2=cmds.optionVar(q="playblastHeight"), parent = self.writeLayout)
		self.scaleSlider = cmds.floatSliderGrp(label="Scale :  ", w=250,cw=([1,65],[2,35],[3,140]),cal=([1,"left"],[2,"left"]),field=True,value = cmds.optionVar(q="playblastScale"),min=0,max=1, parent = self.writeLayout)
		self.padSlider = cmds.intSliderGrp(label="Pad :  ", w=250,cw=([1,65],[2,35],[3,140]),cal=([1,"left"],[2,"left"]),field=True,value = cmds.optionVar(q="playblastPadding"),min=0,max=4, parent = self.writeLayout,visible=False)
		cmds.separator(style="in",h=2,w=275, parent = self.writeLayout)
		cmds.rowLayout(nc=2,cw=([1,225],[2,100]), parent = self.writeLayout)
		self.rangeField = cmds.intFieldGrp( numberOfFields=2, label = 'Frame Range', w=225, cw=([1,65],[2,75],[3,75]), value1=cmds.playbackOptions(q=1,min=1),value2=cmds.playbackOptions(q=1,max=1))
		cmds.button(label = "Set to Timeline",w=100, c=lambda x:cmds.intFieldGrp( self.rangeField,edit=True, value1=cmds.playbackOptions(q=1,min=1),value2=cmds.playbackOptions(q=1,max=1)))
		cmds.separator(style="in",h=2,w=275, parent = self.writeLayout)
		cmds.text(label=" Comment :", parent = self.writeLayout)
		self.commentTx = cmds.scrollField(ww=True,w=250,h=100, parent = self.writeLayout)
		cmds.separator(style="in",h=2,w=275, parent = self.writeLayout)
		cmds.button(label = "Playblast", w=250,h=25, parent = self.writeLayout, c=partial(playblast(self.currentPath,self.currentProject).perform,self.readSettings,[self.setDefault,self.loadReadTab]))
		cmds.button(label = "Save Settings",w=250, h=25, parent = self.writeLayout, c=self.setDefault)

		self.grammarSwitch()
		self.sizeModeSwitch()
		
		# load option tab
		if cmds.layout(self.optionsScroll,q=True,nch=True) > 0:
			for obj in cmds.layout(self.optionsScroll, q=True, childArray = True):
				cmds.deleteUI(obj)
		
		self.optionLayout = cmds.columnLayout(rs = 4, parent = self.optionsScroll)
		self.defDirTxf = cmds.textFieldGrp(label = "Default directory : ", text = self.currentPath, editable = False,cw=[(1,100),(2,270)])
		self.defNameTxf = cmds.textFieldGrp(label = "Default name : ", text = self.currentProject, editable = False,cw=[(1,100),(2,270)])
		cmds.rowLayout(nc = 2, cw=[(1,70),(2,300)])
		cmds.text(label = " Directories", font="boldLabelFont")
		cmds.separator(style='single', w = 295)
		
		self.optRow = cmds.rowLayout(nc=2, parent = self.optionLayout)
		self.addPathTsl = cmds.textScrollList(append = [], w = 182, h = 200, parent = self.optRow,dkc = self.delPath)
		self.nameTsl = cmds.textScrollList(append = [], w = 182, h = 200, parent = self.optRow,dcc = self.projName)
		
		for key in self.location.keys():
			kPath = self.location[key]["path"]
			cmds.textScrollList(self.addPathTsl,e=True,append=[kPath])
			cmds.textScrollList(self.nameTsl,e=True,append=[key])
		
		cmds.button(label = "Add Path...", parent = self.optionLayout, w=370, c=self.addPath)
		cmds.button(label = "Set Default", parent = self.optionLayout, w=370, c=self.setDefaultPath)
		cmds.separator(style='single', w = 370, h = 20, parent = self.optionLayout)
		cmds.button(label = "Save Options", parent = self.optionLayout, w=370, h= 30, c=self.writeOptions)
	
	def loadReadTab(self):
		# load read tab
		#		 delete children
		if cmds.layout(self.readScroll,q=True,nch=True) > 0:
			for obj in cmds.layout(self.readScroll, q=True, childArray = True):
				cmds.deleteUI(obj)
		
		self.blasts = playblast(self.currentPath,self.currentProject).readReg(self.currentPath + "/registry.xml")
		
		self.readCol = cmds.columnLayout(rs=5, parent=self.readScroll)
		self.readLayout = cmds.rowLayout(nc = 2, parent = self.readCol)
		
		self.shotsCol = cmds.columnLayout(w=180,h=280, rs = 5, parent = self.readLayout)
		cmds.text(label = " Shots :")
		self.shotsTsl = cmds.textScrollList(append=sorted(self.blasts.keys()), w=180,h=260, parent = self.shotsCol, sc=self.updateVersion,sii=1)
		
		self.versionsCol = cmds.columnLayout(w=180,h=280, rs = 5, parent = self.readLayout)
		cmds.text(label = " Versions :")
		self.versionsTsl = cmds.textScrollList(w=180,h=260, parent = self.versionsCol, sc=self.updateInfo)
		cmds.text(label = " Informations :", parent = self.readCol)
		self.infoCol = cmds.columnLayout(rs=3, parent = self.readCol)
		self.updateVersion()
		
		
	def updateVersion(self):
		if cmds.textScrollList(self.shotsTsl,q=True,si=True) is not None:
			blast = cmds.textScrollList(self.shotsTsl,q=True,si=True)[0]
			self.versions = playblast(self.currentPath,self.currentProject).read(blast)
			cmds.textScrollList(self.versionsTsl,e=True,removeAll=True)
			cmds.textScrollList(self.versionsTsl,e=True,append=sorted(self.versions.keys()),sii=1)
			self.updateInfo()
		
		
	def updateInfo(self):
		if cmds.layout(self.infoCol,q=True,nch=True) > 0:
			for obj in cmds.layout(self.infoCol, q=True, childArray = True):
				cmds.deleteUI(obj)
		vDic = self.versions[cmds.textScrollList(self.versionsTsl,q=True,si=True)[0]]
		cmds.text(label = " User     :    " + vDic["user"],parent = self.infoCol)
		cmds.text(label = " Date     :    " + vDic["date"][0] + "/" + vDic["date"][1] + "/" + vDic["date"][2] + "   " + vDic["date"][3] + "h"+ vDic["date"][4] + "mn   "+ vDic["date"][5],parent = self.infoCol)
		cmds.text(label = " Frames :    " + vDic["range"][0] + " ; " + vDic["range"][1],parent = self.infoCol)
		cmds.text(label = " Scene : " + vDic["scene"],parent = self.infoCol)
		cmds.separator(h = 7, w=250, style="single",parent = self.infoCol)
		self.vPathTxf = cmds.textFieldGrp(label = "Playblast path : ", parent = self.infoCol, text = vDic["path"], editable = False,cw=[(1,80),(2,270)])
		cmds.button(label = "Open Version", w=130,h=20,c=lambda x:os.system('start ' + vDic["path"]),parent = self.infoCol)
		cmds.button(label = "Open Main file", w=130,h=20,c=lambda x:os.system('start ' + vDic["mPath"]),parent = self.infoCol)
		cmds.separator(h = 7, w=250, style="single",parent = self.infoCol)
		cmds.text(label = " Comment :",parent = self.infoCol)
		cmds.scrollField(text = vDic["comment"],editable=False,w = 200, h=100,parent = self.infoCol)
		
	def setDefaultPath(self,*args):
		index = cmds.textScrollList(self.addPathTsl,q=True,sii=True)[0]
		path = cmds.textScrollList(self.addPathTsl,q=True,si=True)[0]
		
		cmds.textScrollList(self.nameTsl,e=True,sii=index)
		name = cmds.textScrollList(self.nameTsl,q=True,si=True)[0]
		cmds.textFieldGrp(self.defDirTxf,e=True,text=path)
		cmds.textFieldGrp(self.defNameTxf,e=True,text=name)
	
	def addPath(self,*args):
		path = utils().dirBrowse()
		result = cmds.promptDialog(title='Rename Attribute',message='Enter Name:',button=['OK', 'Cancel'],defaultButton='OK',cancelButton='Cancel',dismissString='Cancel')
		if result == 'OK':
			text = cmds.promptDialog(query=True, text=True)
		else:
			text = "unknown"
		cmds.textScrollList(self.addPathTsl, edit=True, append=path)
		cmds.textScrollList(self.nameTsl, edit=True, append=text)
	
	def delPath(self, *args):
		selList = cmds.textScrollList(self.addPathTsl, q=True, sii =True)
		# cmds.textScrollList(self.tgTsl, e=True, rii=selList)
		y = 0
		for x in selList:
			cmds.textScrollList(self.addPathTsl, e=True, rii=x-y)
			cmds.textScrollList(self.nameTsl, e=True, rii=x-y)
			y = y +1
			
	def projName(self, *args):
		index = cmds.textScrollList(self.nameTsl, q=True, sii = True)[0]
		result = cmds.promptDialog(title='Rename Attribute',message='Enter Name:',button=['OK', 'Cancel'],defaultButton='OK',cancelButton='Cancel',dismissString='Cancel')
		if result == 'OK':
			text = cmds.promptDialog(query=True, text=True)
			
		cmds.textScrollList(self.nameTsl, e=True, ap=[index,text])
		cmds.textScrollList(self.nameTsl, e=True, rii=index+1)
		
	def grammarSwitch(self,*args):
		seq = cmds.checkBox(self.seqCbx,q=True,v=True)
		scene = cmds.checkBox(self.sceneCbx,q=True,v=True)
		shot = cmds.checkBox(self.shotCbx,q=True,v=True)
		
		cmds.intField(self.seqField,e=True,en=seq)
		cmds.intField(self.sceneField,e=True,en=scene)
		cmds.intField(self.shotField,e=True,en=shot)
	
	def encodingList(self,*args):
		format = cmds.optionMenuGrp(self.formatOpt,q=True,v=True)
		list = mel.eval('playblast -format "' + format +'" -q -compression')
		
		if cmds.optionMenuGrp(self.encodeOpt,q=True,ils=True) is not None:
			cmds.deleteUI(cmds.optionMenuGrp(self.encodeOpt,q=True,ils=True))
			
		for obj in list:
			cmds.menuItem(label = obj, parent = self.encodeOpt + "|OptionMenu")
			
	def sizeModeSwitch(self,*args):
		if cmds.optionMenuGrp(self.displayOpt,q=True,sl=True) == 1:
			cmds.intFieldGrp(self.displayField,e=True,enable=False)
		else:
			cmds.intFieldGrp(self.displayField,e=True,enable=True)
	
	def readSettings(self,*args):
		# initialize directory
		self.settings = {}
		
		# file name
		self.settings["project"] = cmds.textField(self.projectTxf,q=True,text=True)
		
		self.settings["name"] = self.settings["project"]
		if cmds.checkBox(self.seqCbx,q=True,v=True):
			self.settings["seq"] = cmds.intField(self.seqField,q=True,v=True)
			self.settings["name"] = self.settings["name"] + "_" + str(self.settings["seq"]).zfill(4)
		else:
			self.settings["seq"] = None
		if cmds.checkBox(self.sceneCbx,q=True,v=True):
			self.settings["scene"] = cmds.intField(self.sceneField,q=True,v=True)
			self.settings["name"] = self.settings["name"] + "_" + str(self.settings["scene"]).zfill(4)
		else:
			self.settings["scene"] = None
		if cmds.checkBox(self.shotCbx,q=True,v=True):
			self.settings["shot"] = cmds.intField(self.shotField,q=True,v=True)
			self.settings["name"] = self.settings["name"] + "_" + str(self.settings["shot"]).zfill(4)
		else:
			self.settings["shot"] = None
		
		self.settings["user"] = cmds.textFieldGrp(self.userTxf,q=True,text=True)
		
		# checkboxes
		self.settings["view"] = cmds.checkBox(self.viewCbx,q=True,v=True)
		self.settings["ornaments"] = cmds.checkBox(self.ornamentsCbx,q=True,v=True)
		self.settings["offscreen"] = cmds.checkBox(self.offscreenCbx,q=True,v=True)
		self.settings["multicam"] = cmds.checkBox(self.multicamCbx,q=True,v=True)
		
		# encoding
		self.settings["format"] = cmds.optionMenuGrp(self.formatOpt,q=True,v=True)
		self.settings["encoding"] = cmds.optionMenuGrp(self.encodeOpt,q=True,v=True)
		self.settings["quality"] = cmds.intSliderGrp(self.qualitySlider,q=True,v=True)
		
		# display
		if cmds.optionMenuGrp(self.displayOpt,q=True,sl=True) == 1:
			self.settings["size"] = [0,0]
		else:
			self.settings["size"] = [cmds.intFieldGrp(self.displayField,q=True,value1=True),cmds.intFieldGrp(self.displayField,q=True,value2=True)]
		self.settings["scale"] = cmds.floatSliderGrp(self.scaleSlider,q=True,v=True) * 100
		self.settings["range"] = [cmds.intFieldGrp(self.rangeField,q=True,value1=True),cmds.intFieldGrp(self.rangeField,q=True,value2=True)]
		self.settings["comment"] = cmds.scrollField(self.commentTx,q=True,text=True)
		
		return self.settings
	
	def setDefault(self,*args):
		settings = self.readSettings()
		if settings["seq"] is None:
			v = 0
			settings["seq"] = 0
		else:
			v = 1
		cmds.optionVar(iv=["PBMSeq",v])
		
		if settings["scene"] is None:
			v = 0
			settings["scene"] = 0
		else:
			v = 1
		cmds.optionVar(iv=["PBMScene",v])
		
		if settings["shot"] is None:
			v = 0
			settings["shot"] = 0
		else:
			v = 1
		cmds.optionVar(iv=["PBMShot",v])
		
		cmds.optionVar(iv=["PBMSeqValue",settings["seq"]])
		cmds.optionVar(iv=["PBMSceneValue",settings["scene"]])
		cmds.optionVar(iv=["PBMShotValue",settings["shot"]])
		
		cmds.optionVar(iv=["playblastViewerOn",settings["view"]])
		cmds.optionVar(iv=["playblastShowOrnaments",settings["ornaments"]])
		cmds.optionVar(iv=["playblastOffscreen",settings["offscreen"]])
		cmds.optionVar(iv=["playblastMultiCamera",settings["multicam"]])
		cmds.optionVar(sv=["playblastFormat",settings["format"]])
		cmds.optionVar(sv=["playblastCompression",settings["encoding"]])
		cmds.optionVar(iv=["playblastQuality",settings["quality"]])
		cmds.optionVar(iv=["playblastWidth",settings["size"][0]])
		cmds.optionVar(iv=["playblastHeight",settings["size"][1]])
		cmds.optionVar(fv=["playblastScale",float(settings["scale"])/100])
	
	def readOptions(self):
		optFile = minidom.parse(self.fileLocation + "gf_playblastManager_options.xml")										# parse options
		print self.location.keys()
		for obj in optFile.getElementsByTagName("dir"):																		# add extra directories to the location list
			path = obj.attributes["path"].value
			name = obj.attributes["name"].value
			self.location[name] = {}
			self.location[name]["path"] = path
		
		self.currentPath = optFile.getElementsByTagName("defDir")[0].attributes["path"].value								# current directory
		self.currentProject = optFile.getElementsByTagName("defDir")[0].attributes["name"].value							# current directory
		
	def writeOptions(self,*args):
		doc = minidom.parse(self.fileLocation + "gf_playblastManager_options.xml")										# parse options
		
		root = doc.getElementsByTagName("OPTIONS")[0]
		# remove directories node
		directories = doc.getElementsByTagName("directories")[0]
		root.removeChild(directories)
		
		directories = doc.createElement("directories")
		root.appendChild(directories)
		
		path = cmds.textScrollList(self.addPathTsl,q=True,ai=True)
		name = cmds.textScrollList(self.nameTsl,q=True,ai=True)
		
		for p,n in zip(path,name):
			dir = doc.createElement("dir")
			directories.appendChild(dir)
			dir.setAttribute("path", p)
			dir.setAttribute("name", n)
			
			if not os.path.exists(p + "/archive/"):																# archives folder
				os.makedirs(p + "/archive/")
				
			if not os.path.exists(p + "/registry.xml"):
				reg = minidom.Document()
				rootNode = reg.createElement("REGISTRY")
				reg.appendChild(rootNode)
				
				registerFile = open(p + "/registry.xml", "w")
				registerFile.write(reg.toprettyxml())
				registerFile.close()
		
		defP = cmds.textFieldGrp(self.defDirTxf,q=True,text=True)
		defN = cmds.textFieldGrp(self.defNameTxf,q=True,text=True)
		
		defDir = doc.createElement("defDir")
		directories.appendChild(defDir)
		defDir.setAttribute("path", defP)
		defDir.setAttribute("name", defN)
		
		optionsFile = open(self.fileLocation + "gf_playblastManager_options.xml", "w")
		optionsFile.write(doc.toprettyxml())
		optionsFile.close()
		self.readOptions()
		self.loadTabs()
		
		
class playblast():
	'''
	gf_playblastManager User Interface class
	'''
	def __init__(self,path,project):
		self.path = path
		self.project = project
		
	def perform(self,readSettings,func,*args):
		# read settings
		settings = readSettings()
		if settings["format"] == "image":
			file = self.path + "/" + settings["name"] + "/" + settings["name"]
		else:
			file = self.path + "/" + settings["name"]
		
		# perform playblast
		pb = cmds.playblast(st = settings["range"][0], et = settings["range"][1], filename = file, fo = True, fmt = settings["format"], p=settings["scale"], c=settings["encoding"], qlt = settings["quality"], v=settings["view"], wh=[0,0], orn = settings["ornaments"], os=settings["offscreen"])
		
		# get extension
		list = os.listdir(self.path)
		newList = []
		list.remove("registry.xml")
		for obj in list:
			if settings["name"] in obj:
				newList.append(obj)
		temp = newList[0].split(".")
		if len(temp) > 1:
			ext = "." + newList[0].split(".")[-1]
		else:
			ext = ""
		# check increment
		reg = self.readReg(self.path + "/registry.xml")
		
		if settings["name"] in reg.keys():
			ver = reg[settings["name"]]["version"] +1
		else:
			ver = 0
		list = os.listdir(self.path + "/archive")
		
		# add registry entry
		self.regEntry(settings["name"])
		
		"""
		for obj in list:	# remove non-movie files
			if ".xml" in obj:
				print obj
				list.remove(obj)
		
		for obj in list:
			if not settings["name"] + "_v" in obj:
				list.remove(obj)
		"""
		
		# copy file
		q = str(ver).zfill(4)
		
		if settings["format"] == "image":
			copy = self.path + "/archive/" + settings["name"] + "_v" + q
			source = self.path + "/" + settings["name"]
			print source, copy
			shutil.copytree(source, copy)
			file = self.path + "/" + settings["name"]
		else:
			copy = self.path + "/archive/" + settings["name"] + "_v" + q + ext
			source = file + ext
			print source, copy
			shutil.copy(source, copy)
		
		# write xml entry
		self.write(settings, file + ext, copy)
		func[0]()
		func[1]()
	
	def readReg(self, file):
		if os.path.exists(file):
			blasts = {}
			doc = minidom.parse(file)														# parse register file
			nodes = doc.getElementsByTagName("blast")
			
			for obj in nodes:
				path = obj.attributes["path"].value
				name = obj.attributes["name"].value
				version = obj.attributes["version"].value
				blasts[name] = {"path":path,"version":int(version)}
				
			return blasts
		else:
			return {}
	
	def regEntry(self,name):
		reg = self.readReg(self.path + "/registry.xml")
		file = self.path + "/archive/" + name + ".xml"
		
		if not name in reg.keys():
			doc = minidom.parse(self.path + "/registry.xml")
			rootNode = doc.getElementsByTagName("REGISTRY")[0]
			blastNode = doc.createElement("blast")
			rootNode.appendChild(blastNode)
			
			blastNode.setAttribute("name",name)
			blastNode.setAttribute("path",file)
			blastNode.setAttribute("version","0")
			
			registryFile = open(self.path + "/registry.xml", "w")
			registryFile.write(doc.toprettyxml())
			registryFile.close()
		else:
			doc = minidom.parse(self.path + "/registry.xml")
			nodes = doc.getElementsByTagName("blast")
			for obj in nodes:
				if obj.attributes["name"].value == name:
					ver = int(obj.attributes["version"].value) + 1
					obj.setAttribute("version",str(ver))
			registryFile = open(self.path + "/registry.xml", "w")
			registryFile.write(doc.toprettyxml())
			registryFile.close()
			
	def write(self, settings, filename, archive):
		file = self.path + "/archive/" + settings["name"] + ".xml"
		# initialize file
		if not os.path.exists(file):
			doc = minidom.Document()
			rootNode = doc.createElement("BLAST")
			rootNode.setAttribute("filename",filename)
			rootNode.setAttribute("name",settings["name"])
			doc.appendChild(rootNode)
			
			blastFile = open(file, "w")
			blastFile.write(doc.toprettyxml())
			blastFile.close()
		
		# edit file
		doc = minidom.parse(file)
		
		rootNode = doc.getElementsByTagName("BLAST")[0]
		versionNode = doc.createElement("version")
		rootNode.appendChild(versionNode)
		
		versionNode.setAttribute("path",archive)
		versionNode.setAttribute("user",settings["user"])
		
		dt = datetime.datetime.now()
		versionNode.setAttribute("month",str(dt.month))
		versionNode.setAttribute("day",str(dt.day))
		versionNode.setAttribute("year",str(dt.year))
		versionNode.setAttribute("hour",str(dt.hour))
		versionNode.setAttribute("minute",str(dt.minute))
		versionNode.setAttribute("second",str(dt.second))
		
		versionNode.setAttribute("scene",cmds.file(q=True,sn=True))
		versionNode.setAttribute("comment",settings["comment"])
		
		versionNode.setAttribute("startFrame",str(settings["range"][0]))
		versionNode.setAttribute("endFrame",str(settings["range"][1]))
		
		blastFile = open(file, "w")
		blastFile.write(doc.toprettyxml())
		blastFile.close()
	
	def read(self, name):
		blast = {}
		file = self.path + "/archive/" + name + ".xml"
		doc = minidom.parse(file)
		versions = doc.getElementsByTagName("version")
		for obj in versions:
			vPath = obj.attributes["path"].value
			name = vPath.split("/")[-1]
			blast[name] = {}
			blast[name]["path"] = vPath
			blast[name]["user"] = obj.attributes["user"].value
			blast[name]["range"] = [obj.attributes["startFrame"].value,obj.attributes["endFrame"].value]
			blast[name]["scene"] = obj.attributes["scene"].value
			blast[name]["date"] = [obj.attributes["month"].value,obj.attributes["day"].value,obj.attributes["year"].value,obj.attributes["hour"].value,obj.attributes["minute"].value,obj.attributes["second"].value]
			blast[name]["comment"] = obj.attributes["comment"].value
			blast[name]["mPath"] = doc.getElementsByTagName("BLAST")[0].attributes["filename"].value
			blast[name]["mName"] = doc.getElementsByTagName("BLAST")[0].attributes["name"].value
		return blast
		
class utils():
	'''
	Utilities class
	'''
	def __init__(self):
		pass
		
	#form attach tool	
	def form_attachPosition(self, layout, left, right, top, bottom):
		try:
			self.pLayout = cmds.layout(layout, query=True, p=True)
		except:
			self.pLayout = cmds.control(layout, query=True, p=True)
		cmds.formLayout( self.pLayout, edit=True, attachPosition=[(layout,"left",0,left),(layout,"right",0,right),(layout,"top",0,top),(layout,"bottom",0,bottom)] )
	
	def deleteTsl(self,name, *args):
		for obj in cmds.textScrollList(name,q=True, si=True):
			cmds.textScrollList(name,edit=True,ri=obj)
			
	def addTsl(self, name, *args):
		result = cmds.promptDialog(
                title='Name',
                message='Enter Name:',
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')
		if result == 'OK':
				text = cmds.promptDialog(query=True, text=True)
				cmds.textScrollList(name,edit=True,append = text)
				return text
				
	def createIcon(self, name):
		#active viewport
		view = apiUI.M3dView.active3dView()
		image = api.MImage()
		view.readColorBuffer(image, True)
		image.writeToFile(name, "png")
			
		return name
	
	def strBool(self, value):
		if value == "True":
			return True
		elif value == "False":
			return False
		else:
			return None
	def boolInt(self, value):
		if value == True:
			return 1
		elif value == False:
			return 0
		else:
			return None
			
	def dirBrowse(self):
		return cmds.fileDialog2( cap = "Choose directory", fm=3, okc="OK")[0].replace("\\","\\\\") + "/"