/*
List the available VESA graphics modes.

This program is in the public domain.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#if defined(__linux__)
#include <sys/io.h>
#include <sys/kd.h>
#include <sys/stat.h>
#elif defined(__NetBSD__) || defined(__OpenBSD__)
#include <time.h>
#include <dev/wscons/wsconsio.h>
#include <machine/sysarch.h>
#elif defined(__FreeBSD__)
#include <sys/consio.h>
#include <machine/sysarch.h>
#endif

#include "include/lrmi.h"
#include "vbe2.h"

struct {
	struct vbe_info_block *info;
	struct vbe_mode_info_block *mode;
	char *win; 	/* this doesn't point directly at the window, see update_window() */
	int win_low, win_high;
} vbe;



void
get_ddc(int n)
{
  struct LRMI_regs r;
  char *ddc_level;

  memset(&r, 0, sizeof(r));

  r.eax = 0x4f15;
  
  if (!LRMI_int(0x10, &r)) {
    fprintf(stderr,"Can't get EDID info\n");
  }
  
  if ((r.eax & 0xff) != 0x4f) {
    fprintf(stderr, "VESA VBE not supported\n");
    return;
  }

  switch((r.eax >> 8) & 0xff) {
  case 0:  	    ddc_level = " none";  break;
  case 1:  	    ddc_level = " 1"; break;
  case 2:  	    ddc_level = " 2"; break;
  case 3:  	    ddc_level = " 1 + 2"; break;
  default: ddc_level = "" ;break;
  };

  /*fprintf(stderr," EAX is %08X %s\n", r.eax, ddc_level);*/
  return;
}

int
main(int argc, char *argv[])
{
	struct LRMI_regs r;
	short int *mode_list;
	int i, mode = -1;
#if defined(__NetBSD__) || defined(__OpenBSD__)
	unsigned long iomap[32];
#endif

	if (!LRMI_init())
		return 1;

	vbe.info = LRMI_alloc_real(sizeof(struct vbe_info_block)
	 + sizeof(struct vbe_mode_info_block));

	if (vbe.info == NULL) {
		fprintf(stderr, "Can't alloc real mode memory\n");
		return 1;
	}

	vbe.mode = (struct vbe_mode_info_block *)(vbe.info + 1);

#if 0
	/*
	 Allow read/write to video IO ports
	*/
	ioperm(0x2b0, 0x2df - 0x2b0, 1);
	ioperm(0x3b0, 0x3df - 0x3b0, 1);
#else
	/*
	 Allow read/write to ALL io ports
	*/
#if defined(__linux__)
	ioperm(0, 1024, 1);
	iopl(3);
#elif defined(__NetBSD__) || defined(__OpenBSD__)
	memset(&iomap[0], 0xff, sizeof(iomap));
	i386_set_ioperm(iomap);
	i386_iopl(3);
#elif defined(__FreeBSD__)
	i386_set_ioperm(0, 0x10000, 1);
#endif
#endif

	memset(&r, 0, sizeof(r));

	r.eax = 0x4f00;
	r.es = (unsigned int)vbe.info >> 4;
	r.edi = 0;

	memcpy(vbe.info->vbe_signature, "VBE2", 4);

	if (!LRMI_int(0x10, &r)) {
		fprintf(stderr, "Can't get VESA info (vm86 failure)\n");
		return 1;
	}

	if ((r.eax & 0xffff) != 0x4f || strncmp(vbe.info->vbe_signature, "VESA", 4) != 0) {
		fprintf(stderr, "No VESA bios\n");
		return 1;
	}

	fprintf(stderr,"VBE Version %x.%x\n",
	 (int)(vbe.info->vbe_version >> 8) & 0xff,
	 (int)vbe.info->vbe_version & 0xff);

        fprintf(stderr,"%s\n",
	 (char *)(vbe.info->oem_string_seg * 16 + vbe.info->oem_string_off));

	get_ddc(0);
	mode_list = (short int *)(vbe.info->video_mode_list_seg * 16 + vbe.info->video_mode_list_off);

	while (*mode_list != -1) {
		memset(&r, 0, sizeof(r));

		r.eax = 0x4f01;
		r.ecx = *mode_list;
		r.es = (unsigned int)vbe.mode >> 4;
		r.edi = (unsigned int)vbe.mode & 0xf;

		if (!LRMI_int(0x10, &r)) {
			fprintf(stderr, "Can't get mode info (vm86 failure)\n");
			return 1;
		}

		if (vbe.mode->memory_model == VBE_MODEL_RGB)
			printf("[%3d] %dx%dx%d (%d:%d:%d)\n",
                         *mode_list,
                         vbe.mode->x_resolution,
                         vbe.mode->y_resolution,
                         vbe.mode->red_mask_size+vbe.mode->green_mask_size+vbe.mode->blue_mask_size,
                         vbe.mode->red_mask_size,
                         vbe.mode->green_mask_size,
                         vbe.mode->blue_mask_size);
		else if (vbe.mode->memory_model == VBE_MODEL_256)
			printf("[%3d] %dx%dx8 (256 color palette)\n",
			 *mode_list,
			 vbe.mode->x_resolution,
			 vbe.mode->y_resolution);
		else if (vbe.mode->memory_model == VBE_MODEL_PACKED)
			printf("[%3d] %dx%dx%d (%d color palette)\n",
			 *mode_list,
			 vbe.mode->x_resolution,
			 vbe.mode->y_resolution,
                         vbe.mode->bits_per_pixel,
			 1 << vbe.mode->bits_per_pixel);

		mode_list++;
	}

	LRMI_free_real(vbe.info);

	return 0;
}
