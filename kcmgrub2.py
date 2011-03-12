#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *
from PyKDE4.kio import *
from PyQt4 import uic
import os, locale, re
import pbkdf2


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
    userdiagfile = KStandardDirs.locate("data", "kcmgrub2/userdiag.ui")
    groupdiagfile = KStandardDirs.locate("data", "kcmgrub2/groupdiag.ui")
    self.aboutData=KAboutData(appName, catalogue, programName, version, description, license, copyright, text, homePage, bugEmail)
    self.aboutData.addAuthor(ki18n("Alberto Mattea"), ki18n("Maintainer"))
    self.setAboutData(self.aboutData)
    self.ui=uic.loadUi(uifile, self)
    self.userDiagWidget=QDialog()
    self.userDiag=uic.loadUi(userdiagfile, self.userDiagWidget)
    self.groupDiagWidget=QDialog()
    self.groupDiag=uic.loadUi(groupdiagfile, self.groupDiagWidget)
    self.setButtons(KCModule.Buttons(KCModule.Apply|KCModule.Default))
    self.connectUiElements()
    self.setNeedsAuthorization(True)
    self.defFileOptions={"GRUB_DEFAULT": "0", "GRUB_SAVEDEFAULT": "false", "GRUB_HIDDEN_TIMEOUT": "0", "GRUB_TIMEOUT": "3", "GRUB_HIDDEN_TIMEOUT_QUIET": "true", "GRUB_DISTRIBUTOR": "`lsb_release -i -s 2> /dev/null || echo Debian`", "GRUB_CMDLINE_LINUX_DEFAULT": "\"quiet splash\"", "GRUB_TERMINAL": "gfxterm", "GRUB_GFXMODE": "640x480", "GRUB_DISABLE_LINUX_UUID": "false", "GRUB_DISABLE_LINUX_RECOVERY": "\"false\"", "GRUB_BACKGROUND": "", "GRUB_DISABLE_OS_PROBER": "false"}
    self.defOtherOptions={"memtest": "true", "memtestpath": "/etc/grub.d/" + self.findMemtest() if self.findMemtest() != None else "none"}
    self.fileOptions=self.defFileOptions.copy()
    self.otherOptions=self.defOtherOptions.copy()

  
  def changed(self):
    self.emit(SIGNAL("changed(bool)"), True)
  
  def save(self):
    self.setEnabled(False)
    outFile=self.generateCfgfile()
    self.updateGrubd()
    #for item in self.grubd.values(): print(item)
    self.action=self.authAction()
    self.action.watcher().progressStep.connect(self.showProgress)
    args={"cfgFile": outFile, "memtestOn": self.otherOptions["memtest"], "memtestPath": self.otherOptions["memtestpath"], "grubd": self.grubd}
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
      self.parseGrubd()
      self.loadSettings()
      self.setEnabled(True)
    except:
      KMessageBox.error(self, i18n("Error: cannot open Grub configuration files. Make sure Grub is installed correctly."))    
      raise
  
  def defaults(self):
    self.fileOptions=self.defFileOptions.copy()
    self.otherOptions=self.defOtherOptions.copy()
    self.loadSettings()
    self.ui.secEnabled.setChecked(False)
  
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
    self.cfgFile=open("/etc/default/grub").readlines()
    for line in self.cfgFile:
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
    ### General ###
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
    if "splash" in self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"]:  self.ui.showSplash.setChecked(True)
    else: self.ui.showSplash.setChecked(False)
    if "quiet" in self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"]: self.ui.quietBoot.setChecked(True)
    else: self.ui.quietBoot.setChecked(False)
    ### Advanced ###
    self.ui.distributor.setText(self.fileOptions["GRUB_DISTRIBUTOR"])
    self.ui.gfxMode.setText(self.fileOptions["GRUB_GFXMODE"])
    self.ui.cmdlineLinuxDefault.setText(self.fileOptions["GRUB_CMDLINE_LINUX_DEFAULT"].strip("\" "))
    if self.fileOptions["GRUB_TERMINAL"]=="console": self.ui.disableGfxterm.setChecked(True)
    else: self.ui.disableGfxterm.setChecked(False)
    if self.fileOptions["GRUB_DISABLE_LINUX_UUID"]=="true": self.ui.disableLinuxUUID.setChecked(True)
    else: self.ui.disableLinuxUUID.setChecked(False)
    if self.fileOptions["GRUB_DISABLE_LINUX_RECOVERY"]=="\"true\"": self.ui.disableLinuxRecovery.setChecked(True)
    else: self.ui.disableLinuxRecovery.setChecked(False)
    if self.fileOptions["GRUB_DISABLE_OS_PROBER"]=="true": self.ui.disableOsprober.setChecked(True)
    else: self.ui.disableOsprober.setChecked(False)
    if self.otherOptions["memtest"]=="false": self.ui.disableMemtest.setChecked(True)
    else: self.ui.disableMemtest.setChecked(False)
    if self.otherOptions["memtestpath"]=="none": self.ui.disableMemtest.setEnabled(False)
    else: self.ui.disableMemtest.setEnabled(True)
    self.ui.gfxMode.setEnabled(not self.ui.disableGfxterm.isChecked())
    self.ui.label_3.setEnabled(not self.ui.disableGfxterm.isChecked())
    self.generateBootList()
    ### Security ###
    self.populateUsersTable()
    self.populateGroupsTable()
    if len(self.security["superusers"])>0: self.ui.secEnabled.setChecked(True)
    self.ui.users.setHorizontalHeaderLabels((i18n("Name"), i18n("Superuser"), i18n("Password type")))
    self.ui.groups.setHorizontalHeaderLabels((i18n("Name"), i18n("Locked"), i18n("Allowed users")))
    self.ui.usersGroup.setEnabled(self.ui.secEnabled.isChecked())
    self.ui.groupsGroup.setEnabled(self.ui.secEnabled.isChecked())
    self.updateButtons()
  
  def populateUsersTable(self):
    self.ui.users.setRowCount(0)
    for item in self.security["users"].items():
      self.ui.users.insertRow(self.ui.users.rowCount())
      for x in range(3):
        self.ui.users.setCellWidget(self.ui.users.rowCount()-1, x, QLabel())
        self.ui.users.cellWidget(self.ui.users.rowCount()-1, x).setAlignment(Qt.AlignCenter)
      self.ui.users.cellWidget(self.ui.users.rowCount()-1, 0).setText(item[0])
      self.ui.users.cellWidget(self.ui.users.rowCount()-1, 1).setText(i18n("Yes") if item[0] in self.security["superusers"] else i18n("No"))
      self.ui.users.cellWidget(self.ui.users.rowCount()-1, 2).setText(i18n("Crypted") if item[1][0] else i18n("Plaintext"))
  
  def populateGroupsTable(self):
    self.ui.groups.setRowCount(0)
    for item in sorted(self.security["groups"].items(), key=lambda x: x[0]):
      self.ui.groups.insertRow(self.ui.groups.rowCount())
      for x in range(3):
        self.ui.groups.setCellWidget(self.ui.groups.rowCount()-1, x, QLabel())
        self.ui.groups.cellWidget(self.ui.groups.rowCount()-1, x).setAlignment(Qt.AlignCenter)
      self.ui.groups.cellWidget(self.ui.groups.rowCount()-1, 0).setText(item[0])
      self.ui.groups.cellWidget(self.ui.groups.rowCount()-1, 1).setText(i18n("Yes") if item[1][0] else i18n("No"))
      self.ui.groups.cellWidget(self.ui.groups.rowCount()-1, 2).setText(",".join(item[1][1]) if item[1][0] else i18n("Everyone"))
      if self.ui.groups.cellWidget(self.ui.groups.rowCount()-1, 2).text()=="":
        self.ui.groups.cellWidget(self.ui.groups.rowCount()-1, 2).setText(i18n("Superusers only"))
  
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
  
  def parseGrubd(self):
    items=os.listdir("/etc/grub.d/")
    self.grubd=dict()
    for item in items:
      if item != "README": self.grubd[item]=open("/etc/grub.d/" + item).read()
    self.security=dict()
    self.security["superusers"]=self.getSuperUsers()
    self.security["users"]=self.getUsers()
    self.security["groups"]=self.getGroups()
  
  def getSuperUsers(self):
    superusers=list()
    regex=re.compile(r'set superusers ?= ?"?([a-zA-Z0-9,]{1,})"?')
    for candidate in self.grubd.items():
      curusers=list()
      if regex.search(candidate[1]):
        curusersgroups=regex.findall(candidate[1])
        for curusersgroup in curusersgroups: curusers.extend(curusersgroup.split(","))
      superusers.extend(curusers)
    return superusers
  
  def getUsers(self):
    users=dict()
    cryptoreg=re.compile(r"password_pbkdf2 ([a-zA-Z0-9]{1,}) ([^\n #]+)")
    plainreg=re.compile(r"password ([a-zA-Z0-9]{1,}) ([^\n #]+)")
    for candidate in self.grubd.items():  
      cryptolist=cryptoreg.findall(candidate[1])
      plainlist=plainreg.findall(candidate[1])
      for item in cryptolist: users[item[0]]=[True, item[1]]
      for item in plainlist: users[item[0]]=[False, item[1]]
    return users
  
  def getGroups(self):
    groups=dict()
    lockedregex=re.compile(r'menuentry.+--users "?[a-zA-Z0-9,]{0,}"? .*{')
    unlockedregex=re.compile(r"menuentry.+{")
    usersregex=re.compile(r'--users "?([a-zA-Z0-9,]{0,})"? {')
    for candidate in self.grubd.items():
      users=list()
      if lockedregex.search(candidate[1]):
        if usersregex.search(candidate[1]):
          usergroups=usersregex.findall(candidate[1])
          for usergroup in usergroups: users.extend(usergroup.split(","))
        groups[candidate[0]]=[True, list(set(users))] # Remove duplicates on-the-go
      elif unlockedregex.search(candidate[1]): groups[candidate[0]]=[False, list()]
    return groups
  
  def populateUsersConfig(self, group):
    self.groupDiag.users.selectedListWidget().clear()
    self.groupDiag.users.availableListWidget().clear()
    self.groupDiag.users.selectedListWidget().addItems(self.security["groups"][group][1])
    for item in self.security["users"].keys():
      if item not in self.security["groups"][group][1]: self.groupDiag.users.availableListWidget().addItem(item)
  
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
  
  def updateDisableOsprober(self, state):
    self.fileOptions["GRUB_DISABLE_OS_PROBER"]="true" if state else "false"
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
  
  def updateSecEnabled(self, state):
    self.ui.usersGroup.setEnabled(state)
    self.ui.groupsGroup.setEnabled(state)
    self.ui.userDel.setEnabled(self.ui.users.rowCount()>0)
    self.ui.userMod.setEnabled(self.ui.users.rowCount()>0)
    self.changed()
  
  def updateLocked(self, state):
    self.groupDiag.users.setEnabled(state)
  
  def updateButtons(self):
    if self.ui.users.rowCount()==0 or len(self.ui.users.selectedRanges())==0:
      self.ui.userDel.setEnabled(False)
      self.ui.userMod.setEnabled(False)
    else:
      self.ui.userDel.setEnabled(True)
      self.ui.userMod.setEnabled(True)
    if self.ui.groups.rowCount()==0 or len(self.ui.groups.selectedRanges())==0: self.ui.groupMod.setEnabled(False)
    else: self.ui.groupMod.setEnabled(True)
  
  def generateCfgfile(self):
    out=list()
    usedsettings=list()
    for line in self.cfgFile:
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
  
  def updateGrubd(self):
    items=sorted(self.grubd.items(), key=lambda x: x[0])
    outitems=list()
    for item in items: outitems.append([item[0], list()])
    regex1=re.compile(r'set superusers ?= ?"?[a-zA-Z0-9,]{1,}"?')
    regex2=re.compile(r"password_pbkdf2 [a-zA-Z0-9]{1,} [^\n #]+")
    regex3=re.compile(r"password [a-zA-Z0-9]{1,} [^\n #]+")
    for line in items[0][1].splitlines():
      if not (regex1.search(line) or regex2.search(line) or regex3.search(line)): outitems[0][1].append(line)
    if self.ui.secEnabled.isChecked():
      if outitems[0][1][-1].strip()!="EOF": outitems[0][1].append("cat <<EOF")
      else: del outitems[0][1][-1]
      outitems[0][1].append('set superusers="{0}"'.format(",".join(self.security["superusers"])))
      for user in self.security["users"].items():
        outitems[0][1].append("password{0} {1} {2}".format("_pbkdf2" if user[1][0] else "", user[0], user[1][1]))
      outitems[0][1].append("EOF")
    entryregex1=re.compile(r"(menuentry.+)--users.*{")
    entryregex2=re.compile(r"(menuentry.+){")
    entryregex3=re.compile(r'(printf.+"menuentry.+)--users.*{\\n')
    entryregex4=re.compile(r'(printf.+"menuentry.+){\\n')
    for x in range(1, len(outitems)):
      for line in items[x][1].splitlines():
        if not (entryregex1.search(line) or entryregex2.search(line) or entryregex3.search(line) or entryregex4.search(line)): toappend=line          
        elif self.security["groups"][outitems[x][0]][0] and self.ui.secEnabled.isChecked():
          users='"'+",".join(self.security["groups"][outitems[x][0]][1])+'"'
          if entryregex3.search(line):
            toappend=entryregex3.sub(r"\1--users {0} {{\\n".format(users), line)
          elif entryregex4.search(line):
            toappend=entryregex4.sub(r"\1--users {0} {{\\n".format(users), line)
          elif entryregex1.search(line):
            toappend=entryregex1.sub(r"\1--users {0} {{".format(users), line)
          elif entryregex2.search(line):
            toappend=entryregex2.sub(r"\1--users {0} {{".format(users), line)
        else:
          if entryregex3.search(line):
            toappend=entryregex3.sub(r"\1{\\n", line)
          elif entryregex4.search(line):
            toappend=entryregex4.sub(r"\1{\\n", line)
          elif entryregex1.search(line):
            toappend=entryregex1.sub(r"\1{", line)
          elif entryregex2.search(line):
            toappend=entryregex2.sub(r"\1{", line)
        outitems[x][1].append(toappend)
    for item in outitems: self.grubd[item[0]]="\n".join(item[1])
  
  def showAddUser(self):
    self.userDiag.userConfirm.setEnabled(False)
    self.userDiag.show()
  
  def showModUser(self):
    self.userDiag.userConfirm.setEnabled(False)
    username=str(self.ui.users.cellWidget(self.ui.users.currentRow(), 0).text())
    self.userDiag.userName.setText(username)
    self.userDiag.superUser.setChecked(True if username in self.security["superusers"] else False)
    self.userDiag.show()
  
  def showModGroup(self):
    groupname=str(self.ui.groups.cellWidget(self.ui.groups.currentRow(), 0).text())
    self.groupDiag.locked.setChecked(True if self.security["groups"][groupname][0] else False)
    self.groupDiag.users.setEnabled(self.groupDiag.locked.isChecked())
    self.populateUsersConfig(groupname)
    self.groupDiag.show()
  
  def modUser(self):
    username=str(self.userDiag.userName.text())
    if self.userDiag.cryptPass.isChecked():
      self.worker=WorkThread(username, str(self.userDiag.password.text()))
      self.worker.started.connect(self.showCryptProgress)
      self.worker.finished.connect(self.completeModUser1)
      self.worker.start()
    else:
      password=str(self.userDiag.password.text())
      self.completeModUser2(username, password)
  
  def completeModUser1(self, salt, crypt, username):
    self.worker.started.disconnect(self.showCryptProgress)
    self.worker.finished.disconnect(self.completeModUser1)
    password="grub.pbkdf2.sha512.10000.{0}.{1}".format(salt, crypt)
    self.completeModUser2(username, password)
    self.cprg.close()
  
  def completeModUser2(self, username, password):
    self.security["users"][username]=(self.userDiag.cryptPass.isChecked(), password)
    if self.userDiag.superUser.isChecked() and (username not in self.security["superusers"]): self.security["superusers"].append(str(username))
    elif (not self.userDiag.superUser.isChecked()) and (username in self.security["superusers"]): self.security["superusers"].remove(username)
    self.populateUsersTable()
    self.updateButtons()
    self.userDiag.userName.clear()
    self.userDiag.password.clear()
    self.userDiag.passwordConfirm.clear()
    self.userDiag.superUser.setChecked(False)
    self.userDiag.cryptPass.setChecked(False)
    self.changed()
  
  def delUser(self):
    username=str(self.ui.users.cellWidget(self.ui.users.currentRow(), 0).text())
    self.ui.users.removeRow(self.ui.users.currentRow())
    del self.security["users"][username]
    if username in self.security["superusers"]: self.security["superusers"].remove(username)
    for item in self.security["groups"].keys():
      if username in self.security["groups"][item][1]: self.security["groups"][item][1].remove(username)
    self.populateGroupsTable()
    self.updateButtons()
    self.changed()
  
  def modGroup(self):
    groupname=str(self.ui.groups.cellWidget(self.ui.groups.currentRow(), 0).text())
    if self.groupDiag.locked.isChecked():
      self.security["groups"][groupname][0]=True
      self.security["groups"][groupname][1]=list()
      for item in xrange(self.groupDiag.users.selectedListWidget().count()):
        self.security["groups"][groupname][1].append(str(self.groupDiag.users.selectedListWidget().item(item).text()))
    else:
      self.security["groups"][groupname][0]=False
      self.security["groups"][groupname][1]=list()
    self.populateGroupsTable()
    self.updateButtons()
    self.changed()
      
  def showCryptProgress(self):
    self.cprg=KProgressDialog(self, i18n("Bootloader"), i18n("Crypting password..."))
    self.cprg.setMinimumDuration(0)
    self.cprg.setModal(True)
    self.cprg.setAllowCancel(False)
    self.cprg.progressBar().setMaximum(0)
  
  def dataCheck(self):
    user=str(self.userDiag.userName.text()).strip()
    password1=str(self.userDiag.password.text()).strip()
    password2=str(self.userDiag.passwordConfirm.text()).strip()
    if password1==password2 and password1!="" and user!="": self.userDiag.userConfirm.setEnabled(True)
    else: self.userDiag.userConfirm.setEnabled(False)
  
  def connectUiElements(self):
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
    self.ui.secEnabled.stateChanged.connect(self.updateSecEnabled)
    self.ui.disableMemtest.stateChanged.connect(self.updateDisableMemtest)
    self.ui.disableOsprober.stateChanged.connect(self.updateDisableOsprober)
    self.ui.distributor.textEdited.connect(self.updateDistributor)
    self.ui.gfxMode.textEdited.connect(self.updateGfxMode)
    self.ui.autoStartTimeout.valueChanged.connect(self.updateAutoStartTimeout)
    self.ui.bgImage.textChanged.connect(self.updateBgImage)
    self.ui.bgImage.urlSelected.connect(self.updateBgImage)
    self.ui.userAdd.clicked.connect(self.showAddUser)
    self.ui.userDel.clicked.connect(self.delUser)
    self.ui.userMod.clicked.connect(self.showModUser)
    self.ui.groupMod.clicked.connect(self.showModGroup)
    self.userDiag.userName.textEdited.connect(self.dataCheck)
    self.userDiag.password.textEdited.connect(self.dataCheck)
    self.userDiag.passwordConfirm.textEdited.connect(self.dataCheck)
    self.userDiag.userConfirm.clicked.connect(self.userDiag.close)
    self.userDiag.userConfirm.clicked.connect(self.modUser)
    self.userDiag.userCancel.clicked.connect(self.userDiag.close)
    self.groupDiag.groupConfirm.clicked.connect(self.groupDiag.close)
    self.groupDiag.groupConfirm.clicked.connect(self.modGroup)
    self.groupDiag.groupCancel.clicked.connect(self.groupDiag.close)
    self.groupDiag.locked.stateChanged.connect(self.updateLocked)
    self.ui.users.clicked.connect(self.updateButtons)
    self.ui.groups.clicked.connect(self.updateButtons)

class WorkThread(QThread):
  started=pyqtSignal()
  finished=pyqtSignal(str, str, str)
  def __init__(self, username, clearpw):
    self.username=username
    self.clearpw=clearpw
    QThread.__init__(self)
  def run(self):
    self.emit(SIGNAL('started()'))
    salt, crypt=pbkdf2.pbkdf2(self.clearpw)
    self.emit(SIGNAL('finished(QString, QString, QString)'), salt, crypt, self.username)
    return


def CreatePlugin(widget_parent, parent, component_data):
  KGlobal.locale().insertCatalog("kcmgrub2")
  return PyKcm(component_data, widget_parent)

