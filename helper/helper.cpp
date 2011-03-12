#include "helper.h"
#include <stdio.h>
#include <sys/stat.h>
#include <KProcess>

ActionReply Grub2Helper::save(const QVariantMap &args)
{
  HelperSupport::progressStep(1);
  int ret, i;
  KProcess updProcess; // update-grub
  FILE* fp;
  int maplen=args["grubd"].toMap().count();
  QList<QString> keys=args["grubd"].toMap().keys();
  fp=fopen("/etc/default/grub","w");
  if (!fp) {
    ret=1;
    goto finish;
  }
  fputs(args["cfgFile"].toString().toAscii().constData(), fp);
  fclose(fp);
  if (chdir("/etc/grub.d/") != 0)
  {
    ret=2;
    goto finish;
  }
  for (i=0;i<maplen;i++) {
    fp=fopen(keys[i].toAscii().constData(),"w");
    if (!fp) {
      ret=1;
      goto finish;
    }
    fputs(args["grubd"].toMap().values()[i].toString().toAscii().constData(), fp);
    fclose(fp);
  }
  if (args["memtestPath"].toString() != "none") {
    if (args["memtestOn"].toString() == "true") {
      if (chmod(args["memtestPath"].toString().toAscii().constData(), S_IRUSR | S_IWUSR | S_IXUSR | S_IRGRP | S_IXGRP | S_IROTH | S_IXOTH) != 0) {
        ret=2;
        goto finish;
      }
    } else {
      if (chmod(args["memtestPath"].toString().toAscii().constData(), S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH) != 0) {
        ret=2;
        goto finish;
      }
    }
  }
  updProcess.setShellCommand("update-grub");
  ret=updProcess.execute();
  if (chmod("/boot/grub/grub.cfg", S_IRUSR | S_IRGRP | S_IROTH) != 0) { // We need read access to grub.cfg
    if (chmod("/grub/grub.cfg", S_IRUSR | S_IRGRP | S_IROTH) != 0) { //BSD
      ret=2;
      goto finish;
    }
  }
  finish:
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
    if (chmod("/grub/grub.cfg", S_IRUSR | S_IRGRP | S_IROTH) != 0) { //BSD
      ret=2;
      goto finish;
    }
  }
  finish:
  if (ret == 0) {
    return ActionReply::SuccessReply;
  } else {
    ActionReply reply(ActionReply::HelperError);
    reply.setErrorCode(ret);
    return reply;
  }
}

KDE4_AUTH_HELPER_MAIN("org.kde.kcontrol.kcmgrub2", Grub2Helper)

