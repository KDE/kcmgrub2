include_directories(${VBETEST_SOURCE_DIR}/x86emu/x86emu ${VBETEST_SOURCE_DIR}/x86emu)
add_library(libx86emu STATIC debug.c decode.c fpu.c ops.c ops2.c prim_ops.c sys.c) 
