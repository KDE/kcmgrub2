#include <stdio.h>
#include <sys/stat.h>
#include <KProcess>
#include <QFile>
#include <QDebug>
#include <unistd.h>

#include "helper.h"

int Grub2Helper::writeGrubcfg(const char data[])
{
  FILE* fp;
  fp=fopen("/etc/default/grub","w");
  if (!fp)
    return 1;
  fputs(data, fp);
  fclose(fp);
  return 0;
}

int Grub2Helper::writeScripts(QMap<QString, QVariant> map)
{
  int maplen=map.count();
  int i;
  FILE* fp;
  QList<QString> keys=map.keys();
  if (chdir("/etc/grub.d/") != 0)
    return 2;
  for (i=0;i<maplen;i++) {
    fp=fopen(keys[i].toAscii().constData(),"w");
    if (!fp)
      return 3;
    fputs(map.values()[i].toString().toAscii().constData(), fp);
    fclose(fp);
  }
  if (chmod("09_colors", S_IRUSR | S_IWUSR | S_IXUSR | S_IRGRP | S_IXGRP | S_IROTH | S_IXOTH) != 0)
      return 8;
  return 0;
}

int Grub2Helper::chMemtest(QString path, QString on)
{
  if (path != "none") {
    if (on == "true") {
      if (chmod(path.toAscii().constData(), S_IRUSR | S_IWUSR | S_IXUSR | S_IRGRP | S_IXGRP | S_IROTH | S_IXOTH) != 0)
        return 4;
    } else {
      if (chmod(path.toAscii().constData(), S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH) != 0)
        return 4;
    }
  }
  return 0;
}

int Grub2Helper::doUpdate()
{
  KProcess updProcess;
  QFile mkconfig;
  QString config=findGrubCfg();
  if (config==QString(""))
    return 5;
  QString toexec;
  mkconfig.setFileName("/usr/sbin/grub2-mkconfig");
  if (mkconfig.exists()) {
    toexec.append("/usr/sbin/grub2-mkconfig");
  } else {
    mkconfig.setFileName("/usr/sbin/grub-mkconfig");
    if (mkconfig.exists()) {
      toexec.append("/usr/sbin/grub-mkconfig");
    } else {
      return 5;
    }
  }
  updProcess.setShellCommand(toexec.append(" -o ").append(config));
  if (updProcess.execute()!=0)
    return 5;
  return 0;
}

QString Grub2Helper::findGrubCfg()
{
  QFile file;
  file.setFileName("/grub/grub.cfg");
  if (file.exists())
    return QString("/grub/grub.cfg");
  file.setFileName("/boot/grub2/grub.cfg");
  if (file.exists())
    return QString("/boot/grub2/grub.cfg");
  file.setFileName("/boot/grub/grub.cfg");
  if (file.exists())
    return QString("/boot/grub/grub.cfg");
  return QString("");
}

int Grub2Helper::doInstall(QList<QVariant> devices)
{
  KProcess instProcess;
  int i;
  QFile file;
  QString toexec;
  file.setFileName("/usr/sbin/grub2-install");
  if (file.exists()) {
    toexec.append("/usr/sbin/grub2-install");
  } else {
    file.setFileName("/usr/sbin/grub-install");
    if (file.exists()) {
      toexec.append("/usr/sbin/grub-install");
    } else {
      return 7;
    }
  }
  for (i=0;i<devices.count();i++) {
    QStringList cmd;
    cmd << toexec << devices[i].toString();
    instProcess.setProgram(cmd);
    if(instProcess.execute()!=0)
      return 7;
  }
  return 0;
}

ActionReply Grub2Helper::save(const QVariantMap &args)
{
  int ret;
  HelperSupport::progressStep(1);
  ret=writeGrubcfg(args["cfgFile"].toString().toAscii().constData());
  if (ret!=0)
    goto finish;
  ret=writeScripts(args["grubd"].toMap());
  if (ret!=0)
    goto finish;
  ret=chMemtest(args["memtestPath"].toString(), args["memtestOn"].toString());
  if (ret!=0)
    goto finish;
  ret=doUpdate();
  if (ret!=0)
    goto finish;
  
  HelperSupport::progressStep(2);
  ret=doInstall(args["grubinst"].toList());
   
  finish:
  HelperSupport::progressStep(3);
  if (ret == 0) {
    return ActionReply::SuccessReply;
  } else {
    ActionReply reply(ActionReply::HelperError);
    reply.setErrorCode(ret);
    return reply;
  }
}

ActionReply Grub2Helper::readcfg(const QVariantMap &args)
{
  (void)args; // Fix warning
  ActionReply errorreply(ActionReply::HelperError);
  errorreply.setErrorCode(6);
  QFile file;
  QString config=findGrubCfg();
  file.setFileName(config);
  if (!file.open(QIODevice::ReadOnly)) {
    return errorreply;
  }
  const QByteArray data=file.readAll();
  file.close();
  ActionReply reply(ActionReply::SuccessReply);
  QVariantMap retdata;
  retdata["contents"] = data;
  reply.setData(retdata);
  return reply;
}

ActionReply Grub2Helper::probevbe(const QVariantMap &args)
{
  QProcess probeProcess; // readAllStandardOutput() doesn't seem to work with KProcess
  probeProcess.start(args["vbetest"].toString());
  if (probeProcess.waitForStarted()!=true) {
    ActionReply reply(ActionReply::HelperError);
    reply.setErrorCode(8);
    return reply;
  } else {
    probeProcess.waitForFinished();
    probeProcess.waitForReadyRead();
    const QByteArray output=probeProcess.readAllStandardOutput();
    ActionReply reply(ActionReply::SuccessReply);
    QVariantMap retdata;
    retdata["contents"] = output;
    reply.setData(retdata);
    return reply;
  }
}

KDE4_AUTH_HELPER_MAIN("org.kde.kcontrol.kcmgrub2", Grub2Helper)

