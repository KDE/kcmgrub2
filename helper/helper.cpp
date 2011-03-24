#include <stdio.h>
#include <sys/stat.h>
#include <KProcess>
#include <QDebug>

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
  updProcess.setShellCommand("update-grub");
  if (updProcess.execute()!=0)
    return 5;
  return 0;
}

int Grub2Helper::chGrubcfg()
{
  if (chmod("/boot/grub/grub.cfg", S_IRUSR | S_IRGRP | S_IROTH) != 0) { // We need read access to grub.cfg
    if (chmod("/grub/grub.cfg", S_IRUSR | S_IRGRP | S_IROTH) != 0) // BSD
      return 6;
  }
  return 0;
}

int Grub2Helper::doInstall(QList<QVariant> devices)
{
  KProcess instProcess;
  int i;
  for (i=0;i<devices.count();i++) {
    QStringList cmd;
    cmd << QString("/usr/sbin/grub-install") << devices[i].toString();
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
  ret=chGrubcfg();
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

ActionReply Grub2Helper::fixperm(const QVariantMap &args)
{
  int ret=0;
  if (chmod("/boot/grub/grub.cfg", S_IRUSR | S_IRGRP | S_IROTH) != 0) { // We need read access to grub.cfg
    if (chmod("/grub/grub.cfg", S_IRUSR | S_IRGRP | S_IROTH) != 0) // BSD
      ret=6;
  }
  if (ret == 0) {
    return ActionReply::SuccessReply;
  } else {
    ActionReply reply(ActionReply::HelperError);
    reply.setErrorCode(ret);
    return reply;
  }
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

