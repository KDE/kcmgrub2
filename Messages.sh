#!/bin/sh

# invoke the extractrc script on all .ui, .rc, and .kcfg files in the sources
# the results are stored in a pseudo .cpp file to be picked up by xgettext.
$EXTRACTRC `find . -name \*.rc -o -name \*.ui -o -name \*.kcfg` >> rc.cpp
# call xgettext on all source files.
$XGETTEXT `find . -name \*.cpp -o -name \*.h -o -name \*.py` -o $podir/kcmgrub2.pot
