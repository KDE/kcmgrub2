#project( kcm_grub2 )
find_package( KDE4 REQUIRED )
include(KDE4Defaults)
 
include_directories( ${KDE4_INCLUDES} )

kde4_add_executable(kcmgrub2helper helper.cpp ${helper_mocs})
target_link_libraries(kcmgrub2helper ${KDE4_KDECORE_LIBS})
install(TARGETS kcmgrub2helper DESTINATION ${LIBEXEC_INSTALL_DIR})
kde4_install_auth_helper_files(kcmgrub2helper org.kde.kcontrol.kcmgrub2 root)
kde4_install_auth_actions(org.kde.kcontrol.kcmgrub2 kcmgrub2_actions.actions) 
