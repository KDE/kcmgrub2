#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *
from PyKDE4.kio import *
from PyQt4 import uic
import os, locale

class PyKcm(KCModule):
  def __init__(self, component_data, parent):
    KCModule.__init__(self, component_data, parent)
    self.language = locale.getlocale(locale.LC_MESSAGES)
    self.encoding = locale.getlocale(locale.LC_CTYPE)
    appName     = "kcmgrub2"
    catalogue   = "kcmgrub2"
    programName = ki18n("Grub2 configuration")
    version     = "1.1"
    description = ki18n("Grub2 configuration tool")
    license     = KAboutData.License_GPL_V3
    copyright   = ki18n("(c) 2011 Alberto Mattea")
    text        = KLocalizedString()
    homePage    = "http://kde-apps.org/content/show.php?content=137886"
    bugEmail    = ""
    uifile = KStandardDirs.locate("data", "kcmgrub2/kcmgrub2.ui")
    self.aboutData=KAboutData(appName, catalogue, programName, version, description, license, copyright, text, homePage, bugEmail)
    self.aboutData.addAuthor(ki18n("Alberto Mattea"), ki18n("Maintainer"))
    self.setAboutData(self.aboutData)
    self.ui=uic.loadUi(uifile, self)
    self.setButtons(KCModule.Buttons(KCModule.Apply|KCModule.Default))
    self.ui.defItem.currentIndexChanged.connect(self.updateDefItem)
    self.ui.showSplash.stateChanged.connect(self.updateCmdlineFromCheckbox1)
    self.ui.quietBoot.stateChanged.connect(self.updateCmdlineFromCheckbox2)
    self.ui.cmdlineLinuxDefault.textEdited.connect(self.updateCmdlineLinuxDefault)
    self.ui.autoStart.stateChanged.connect(self.updateAutoStart)
    self.ui.showBgImage.stateChanged.connect(self.updateShowBgImage)
    self.ui.showCountdown.stateChanged.connect(self.updateShowCountdown)
    self.ui.noHidden.stateChanged.connect(self.updateNoHidden)
    self.ui.disableGfxterm.stateChanged.connect(self.updateDisableGfxterm)
    self.ui.disableLinuxUUID.stateChanged.connect(self.updateDisableLinuxUUID)
    self.ui.disableLinuxRecovery.stateChanged.connect(self.updateDisableLinuxRecovery)
    self.ui.disableMemtest.stateChanged.connect(self.updateDisableMemtest)
    self.ui.distributor.textEdited.connect(self.updateDistributor)
    self.ui.gfxMode.textEdited.connect(self.updateGfxMode)
    self.ui.autoStartTimeout.valueChanged.connect(self.updateAutoStartTimeout)
    self.ui.bgImage.textChanged.connect(self.updateBgImage)
    self.ui.bgImage.urlSelected.connect(self.updateBgImage)
    self.setNeedsAuthorization(True)
    self.defFileOptions={"GRUB_DEFAULT": "0", "GRUB_SAVEDEFAULT": "false", "GRUB_HIDDEN_TIMEOUT": "0", "GRUB_TIMEOUT": "3", "GRUB_HIDDEN_TIMEOUT_QUIET": "true", "GRUB_DISTRIBUTOR": "`lsb_release -i -s 2> /dev/null || echo Debian`", "GRUB_CMDLINE_LINUX_DEFAULT": "\"quiet splash\"", "GRUB_TERMINAL": "gfxterm", "GRUB_GFXMODE": "640x480", "GRUB_DISABLE_LINUX_UUID": "false", "GRUB_DISABLE_LINUX_RECOVERY": "\"false\"", "GRUB_BACKGROUND": ""}
    self.defOtherOptions={"memtest": "true", "memtestpath": "/etc/grub.d/" + self.findMemtest() if self.findMemtest() != None else "none"}
    self.fileOptions=self.defFileOptions.copy()
    self.otherOptions=self.defOtherOptions.copy()

  
  def changed(self):
    self.emit(SIGNAL("changed(bool)"), True)
  
  def save(self):
    self.setEnabled(False)
    outFile=self.generateCfgfile()
    self.action=self.authAction()
    self.action.watcher().progressStep.connect(self.showProgress)
    args={"cfgFile": outFile, "memtestOn": self.otherOptions["memtest"], "memtestPath": self.otherOptions["memtestpath"]}
    self.action.setArguments(args)
    self.authSuccessful=False
    reply=self.action.execute()
    if self.authSuccessful: self.prg.close()
    if reply.failed(): KMessageBox.error(self, i18n("Unable to authenticate/execute the action."))
    else: self.load()
    self.setEnabled(True)

  def load(self):
    self.setEnabled(False)
    try:
      self.fileOptions.update(self.getOptionsFromFile())
      self.otherOptions.update(self.getOtherOptions())
      self.currentItems=self.getCurrentItems()
      self.loadSettings()
      self.setEnabled(True)
    except:
      KMessageBox.error(self, i18n("Error: cannot open Grub configuration files. Make sure Grub is installed correctly."))    
      raise
  
  def defaults(self):
    self.fileOptions=self.defFileOptions.copy()
    self.otherOptions=self.defOtherOptions.copy()
    self.loadSettings()
  
  def showProgress(self, state):
    self.authSuccessful=True
    try:
      self.prg.setEnabled(True)
      self.prg.show()
    except:
      self.prg=KProgressDialog(self, i18n("Bootloader"), i18n("Updating grub configuration..."))
      self.prg.setModal(True)
      self.prg.setAllowCancel(False)
      self.prg.progressBar().setMaximum(0)
      self.prg.setMinimumDuration(0)
    
  def getOptionsFromFile(self):
    cfg={}
    lines=open("/etc/default/grub").readlines()
    for line in lines:
      tokens=line.split("=", 1)
      if len(tokens)==2:
        setting=tokens[0].strip()
        value=tokens[1].strip()
        if setting in self.fileOptions.keys(): cfg[setting]=value
    return cfg
  
  def getOtherOptions(self):
    cfg={}
    memtest=self.findMemtest()
    if memtest != None:
      cfg["memtestpath"]="/etc/grub.d/" + memtest
      cfg["memtest"]="true" if os.access(cfg["memtestpath"], os.F_OK | os.R_OK | os.X_OK) else "false"
    else:
      cfg["memtestpath"]="none"
      cfg["memtest"]="false"
    return cfg
  
  def findMemtest(self):
    candidates=os.listdir("/etc/grub.d/")
    for candidate in candidates:
      if "memtest86+" in candidate: return candidate
    return None
  
  def getCurrentItems(self):
    try: lines=open("/boot/grub/grub.cfg").readlines()
    except: lines=open("/grub/grub.cfg").readlines() # NetBSD, OpenBSD
    entries=list()
    for line in lines:
      tokens=line.split()
      if len(tokens)>1 and tokens[0]=="menuentry":
        osname=""
        i=1
        while tokens[i][-1] != "'" and tokens[i][-1] != "\"":
          osname=osname+tokens[i]+" "
          i+=1
        osname+=tokens[i]
        entries.append(osname.strip("\"'"))
    return entries
  
  def loadSettings(self):
    ght=self.fileOptions["GRUB_HIDDEN_TIMEOUT"]
    gt=self.fileOptions["GRUB_TIMEOUT"]
    gb=self.fileOptions["GRUB_BACKGROUND"]
    if self.fileOptions["GRUB_HIDDEN_TIMEOUT_QUIET"]=="false": self.ui.showCountdown.setChecked(True)
    else: self.ui.showCountdown.setChecked(False)
    if ght=="": self.ui.noHidden.setChecked(True)
    elif ght.isdigit():
      self.ui.noHidden.setChecked(False)
      self.ui.autoStart.setChecked(True)
      self.ui.autoStartTimeout.setValue(int(ght))
    if gt.isdigit() and int(gt)>=0:
      self.ui.autoStart.setChecked(True)
      if ght=="": self.ui.autoStartTimeout.setValue(int(gt))
    elif ght=="": self.ui.autoStart.setChecked(False)
    if gb != "":
      self.ui.showBgImage.setChecked(True)
      self.ui.bgImage.setText(gb)
    else: self.ui.showBgImage.setChecked(False)
    self.ui.autoStartTimeout.setEnabled(self.ui.autoStart.isChecked())
    self.ui.bgImage.setEnabled(self.ui.showBgImage.isChecked())
    self.ui.noHidden.setEnabled(self.ui.autoStart.isChecked())
    self.ui.showCountdown.setEnabled(self.ui.autoStart.isChecked())
    self.ui.distributor.setText(self.fileOptions["GRUB_DISTRIBUTOR"])
    self.ui.gfxMode.setText(self.fileOptions["GRUB_GFXMODE"])
    self.ui.cmdlineLinuxDefault.setText(self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"].strip("\" "))
    if "splash" in self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"]:  self.ui.showSplash.setChecked(True)
    else: self.ui.showSplash.setChecked(False)
    if "quiet" in self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"]: self.ui.quietBoot.setChecked(True)
    else: self.ui.quietBoot.setChecked(False)
    if self.fileOptions["GRUB_TERMINAL"]=="console": self.ui.disableGfxterm.setChecked(True)
    else: self.ui.disableGfxterm.setChecked(False)
    if self.fileOptions["GRUB_DISABLE_LINUX_UUID"]=="true": self.ui.disableLinuxUUID.setChecked(True)
    else: self.ui.disableLinuxUUID.setChecked(False)
    if self.fileOptions["GRUB_DISABLE_LINUX_RECOVERY"]=="\"true\"": self.ui.disableLinuxRecovery.setChecked(True)
    else: self.ui.disableLinuxRecovery.setChecked(False)
    if self.otherOptions["memtest"]=="false": self.ui.disableMemtest.setChecked(True)
    else: self.ui.disableMemtest.setChecked(False)
    if self.otherOptions["memtestpath"]=="none": self.ui.disableMemtest.setEnabled(False)
    else: self.ui.disableMemtest.setEnabled(True)
    self.ui.gfxMode.setEnabled(not self.ui.disableGfxterm.isChecked())
    self.ui.label_3.setEnabled(not self.ui.disableGfxterm.isChecked())
    self.generateBootList()
  
  def generateBootList(self):
    gd=self.fileOptions["GRUB_DEFAULT"]
    self.defItem.clear()
    for item in self.currentItems: self.defItem.addItem(item)
    self.defItem.addItem(i18n("Last used"))
    if gd.isdigit():
      if int(gd)<self.defItem.count(): self.defItem.setCurrentIndex(int(gd))
      else:
        gd="0"
        self.defItem.setCurrentIndex(0)
      self.defItem.emit(SIGNAL("currentIndexChanged(int)"), int(gd))
    elif gd=="saved": self.defItem.setCurrentIndex(self.defItem.count()-1)
    elif gd.strip("\"'") in self.currentItems: self.defItem.setCurrentIndex(self.defItem.findText(gd.strip("\"'")))
  
  def updateDefItem(self, state):
    if state==self.defItem.count()-1:
      self.fileOptions["GRUB_DEFAULT"]="saved"
      self.fileOptions["GRUB_SAVEDEFAULT"]="true"
    else:
      if "Linux" in self.defItem.itemText(state): self.fileOptions["GRUB_DEFAULT"]=str(state) # No full names with Linux (version changes)
      else: self.fileOptions["GRUB_DEFAULT"]="'"+str(self.defItem.itemText(state))+"'" # Use full names to avoid reordering problems
      self.fileOptions["GRUB_SAVEDEFAULT"]="false"
    self.changed()
  
  def updateCmdlineFromCheckbox1(self, state):
    if self.ui.showSplash.isChecked():
      if "splash" not in self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"]:
        self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"]="\""+str(self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"].strip("\" ") + " splash").strip()+"\""
    else:
      self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"]=self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"].strip("\" ").replace("splash", "")
      self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"]="\""+self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"].strip()+"\""
    self.ui.cmdlineLinuxDefault.setText(self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"].strip("\" "))
    self.changed()
  
  def updateCmdlineFromCheckbox2(self, state):
    if self.ui.quietBoot.isChecked():
      if "quiet" not in self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"]:
        self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"]="\""+str(self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"].strip("\" ") + " quiet").strip()+"\""
    else:
      self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"]=self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"].strip("\" ").replace("quiet", "")
      self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"]="\""+self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"].strip()+"\""
    self.ui.cmdlineLinuxDefault.setText(self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"].strip("\" "))
    self.changed()
  
  def updateCmdlineLinuxDefault(self, state):
    self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"]=str("\""+state+"\"")
    if "splash" in state: self.ui.showSplash.setChecked(True)
    else: self.ui.showSplash.setChecked(False)
    if "quiet" in state: self.ui.quietBoot.setChecked(True)
    else: self.ui.quietBoot.setChecked(False)
    self.changed()
  
  def updateAutoStart(self, state):
    self.ui.autoStartTimeout.setEnabled(state)
    if state:
      self.ui.noHidden.setEnabled(True)
      self.ui.showCountdown.setEnabled(True)
      if self.ui.noHidden.isChecked():
        self.fileOptions["GRUB_TIMEOUT"]=str(self.ui.autoStartTimeout.value())
      else:
        self.fileOptions["GRUB_TIMEOUT"]="3"
        self.fileOptions["GRUB_HIDDEN_TIMEOUT"]=str(self.ui.autoStartTimeout.value())
    else:
      self.fileOptions["GRUB_TIMEOUT"]="-1"
      self.fileOptions["GRUB_HIDDEN_TIMEOUT"]=""
      self.ui.noHidden.setChecked(True)
      self.ui.noHidden.setEnabled(False)
      self.ui.showCountdown.setChecked(False)
      self.ui.showCountdown.setEnabled(False)
    self.changed()
  
  def updateShowBgImage(self, state):
    self.ui.bgImage.setEnabled(state)
    if state: self.fileOptions["GRUB_BACKGROUND"]=str(self.ui.bgImage.text())
    else: self.fileOptions["GRUB_BACKGROUND"]=""
    self.changed()
  
  def updateShowCountdown(self, state):
    self.fileOptions["GRUB_HIDDEN_TIMEOUT_QUIET"]="false" if state else "true"
    self.changed()
  
  def updateNoHidden(self, state):
    if state:
      self.fileOptions["GRUB_HIDDEN_TIMEOUT"]=""
      self.fileOptions["GRUB_TIMEOUT"]=str(self.ui.autoStartTimeout.value())
    else: self.fileOptions["GRUB_HIDDEN_TIMEOUT"]=str(self.ui.autoStartTimeout.value())
    self.changed()
  
  def updateDisableGfxterm(self, state):
    if state:
      self.ui.label_3.setEnabled(False)
      self.ui.gfxMode.setEnabled(False)
    else:
      self.ui.label_3.setEnabled(True)
      self.ui.gfxMode.setEnabled(True)
    self.fileOptions["GRUB_TERMINAL"]="console" if state else "gfxterm"
    self.changed()
  
  def updateDisableLinuxUUID(self, state):
    self.fileOptions["GRUB_DISABLE_LINUX_UUID"]="true" if state else "false"
    self.changed()
  
  def updateDisableLinuxRecovery(self, state):
    self.fileOptions["GRUB_DISABLE_LINUX_RECOVERY"]="\"true\"" if state else "false"
    self.changed()
    
  def updateDisableMemtest(self, state):
    self.otherOptions["memtest"]="false" if state else "true"
    self.changed()
  
  def updateDistributor(self, state):
    self.fileOptions["GRUB_DISTRIBUTOR"]=str(self.ui.distributor.text())
    self.changed()
  
  def updateGfxMode(self, state):
    self.fileOptions["GRUB_GFXMODE"]=str(self.ui.gfxMode.text())
    self.changed()
  
  def updateAutoStartTimeout(self, state):
    if self.fileOptions["GRUB_HIDDEN_TIMEOUT"]=="":
      self.fileOptions["GRUB_TIMEOUT"]=str(self.ui.autoStartTimeout.value())
    else:
      self.fileOptions["GRUB_HIDDEN_TIMEOUT"]=str(self.ui.autoStartTimeout.value())
    self.changed()
  
  def updateBgImage(self, state):
    if type(state)==KUrl: self.fileOptions["GRUB_BACKGROUND"]=str(state.path())
    else: self.fileOptions["GRUB_BACKGROUND"]=str(state)
    self.changed()
  
  def generateCfgfile(self):
    lines=open("/etc/default/grub").readlines()
    out=list()
    usedsettings=list()
    for line in lines:
      l=line.strip()
      if len(l)>0:
        if l[0]=="#": st=l[1:].split("=")[0].strip()
        else: st=l.split("=")[0].strip()
        if st in self.fileOptions.keys():
          out.append(st+"="+self.fileOptions[st])
          usedsettings.append(st)
        else: out.append(l)
      else: out.append("")
    out.append("")
    for setting in self.fileOptions.keys():
      if setting not in usedsettings: out.append(setting+"="+self.fileOptions[setting]+"\n")
    return "\n".join(out)

def CreatePlugin(widget_parent, parent, component_data):
  KGlobal.locale().insertCatalog("kcmgrub2")
  return PyKcm(component_data, widget_parent)

