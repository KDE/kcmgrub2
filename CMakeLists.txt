project( kcmgrub2 )
add_subdirectory (helper)
add_subdirectory (i18n)
find_package( KDE4 REQUIRED )
include(KDE4Defaults)
include(FindPythonLibrary)
include(FindPyQt4)
include(FindPyKDE4)
 
install(FILES kcmgrub2.py kcmgrub2.ui DESTINATION ${DATA_INSTALL_DIR}/kcmgrub2)

kde4_install_icons(${ICON_INSTALL_DIR})
install(FILES kcmgrub2.desktop DESTINATION ${SERVICES_INSTALL_DIR})
