#include "helper.h"
#include <stdio.h>
#include <sys/stat.h>
#include <KProcess>

ActionReply Grub2Helper::save(const QVariantMap &args)
{
  HelperSupport::progressStep(1);
  int ret; // error code
  KProcess updProcess; // update-grub
  FILE* fp;
  fp=fopen("/etc/default/grub","w");
  if (!fp) {
    ret=1;
    goto finish;
  }
  fputs(args["cfgFile"].toString().toAscii().constData(), fp);
  fclose(fp);
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

