#ifndef KCM_GRUB2_HELPER_H
#define KCM_GRUB2_HELPER_H

#include <kauth.h>
#include <stdio.h>

using namespace KAuth;

class Grub2Helper : public QObject
{
    Q_OBJECT

    public slots:
      ActionReply save(const QVariantMap &map);
      ActionReply readcfg(const QVariantMap &map);
      ActionReply probevbe(const QVariantMap &map);
    private:
      int writeGrubcfg(const char data[]);
      int writeScripts(QMap<QString, QVariant> map);
      int chMemtest(QString path, QString on);
      int doUpdate();
      QString findGrubCfg();
      int doInstall(QList<QVariant> devices);
};
#endif
