#ifndef VBE_H
#define VBE_H

#ident "$Id: vbe.h,v 1.3 2003/02/11 15:33:03 notting Exp $"

#include "common.h"

#include <sys/types.h>

/* Stuff returned by int 0x10, function 0x4f, subfunction 0x01. */
struct vbe_mode_info {
	/* required for all VESA versions */
	struct {
		/* VBE 1.0+ */
		u_int16_t supported: 1;
		u_int16_t optional_info_available: 1;
		u_int16_t bios_output_supported: 1;
		u_int16_t color: 1;
		u_int16_t graphics: 1;
		/* VBE 2.0+ */
		u_int16_t not_vga_compatible: 1;
		u_int16_t not_bank_switched: 1;
		u_int16_t lfb: 1;
		/* VBE 1.0+ */
		u_int16_t unknown: 1;
		u_int16_t must_enable_directaccess_in_10: 1;
	} mode_attributes;
	struct {
		unsigned char exists: 1;
		unsigned char readable: 1;
		unsigned char writeable: 1;
		unsigned char reserved: 5;
	} windowa_attributes, windowb_attributes;
	u_int16_t window_granularity;
	u_int16_t window_size;
	u_int16_t windowa_start_segment, windowb_start_segment;
	u_int16_t window_positioning_seg, window_positioning_ofs;
	u_int16_t bytes_per_scanline;
	/* optional for VESA 1.0/1.1, required for OEM modes */
	u_int16_t w, h;
	unsigned char cell_width, cell_height;
	unsigned char memory_planes;
	unsigned char bpp;
	unsigned char banks;
	enum {
		memory_model_text = 0,
		memory_model_cga = 1,
		memory_model_hgc = 2,
		memory_model_ega16 = 3,
		memory_model_packed_pixel = 4,
		memory_model_sequ256 = 5,
		memory_model_direct_color = 6,
		memory_model_yuv = 7,
	} memory_model: 8;
	unsigned char bank_size;
	unsigned char image_pages;
	unsigned char reserved1;
	/* required for VESA 1.2+ */
	unsigned char red_mask, red_field;
	unsigned char green_mask, green_field;
	unsigned char blue_mask, blue_field;
	unsigned char reserved_mask, reserved_field;
	unsigned char direct_color_mode_info;
	/* VESA 2.0+ */
	u_int32_t linear_buffer_address;
	u_int32_t offscreen_memory_address;
	u_int16_t offscreen_memory_size;
	unsigned char reserved2[206];
} __attribute__ ((packed));

#define VBE_LINEAR_FRAMEBUFFER 0x4000

/* Get information about a particular video mode, bitwise or with
   VBE_LINEAR_FRAMEBUFFER to check if LFB version is supported. */
struct vbe_mode_info *vbe_get_mode_info(u_int16_t mode);

/* Get the current video mode, -1 on error. */
int32_t vbe_get_mode();
/* Set a new video mode, bitwise or with VBE_LINEAR_FRAMEBUFFER. */
void vbe_set_mode(u_int16_t mode);

/* Save/restore the SVGA state.  Call free() on the state record when done. */
const void *vbe_save_svga_state();
void vbe_restore_svga_state(const void *state);

#endif /* VBE_H */
