#if defined (__i386__) || defined (__amd64__)
#include <sys/types.h>
#include <sys/io.h>
#include <sys/mman.h>
#include <netinet/in.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>
#include <limits.h>
#include <ctype.h>
#include "common.h"
#include "include/lrmi.h"
#include "vbe.h"
#ident "$Id: vbe.c,v 1.10 2003/02/11 14:47:38 notting Exp $"

/* Return information about a particular video mode. */
struct vbe_mode_info *vbe_get_mode_info(u_int16_t mode)
{
	struct LRMI_regs regs;
	char *mem;
	struct vbe_mode_info *ret = NULL;

	/* Initialize LRMI. */
	if(LRMI_init() == 0) {
		return NULL;
	}

	/* Allocate a chunk of memory. */
	mem = LRMI_alloc_real(sizeof(struct vbe_mode_info));
	if(mem == NULL) {
		return NULL;
	}
	memset(mem, 0, sizeof(struct vbe_mode_info));

	memset(&regs, 0, sizeof(regs));
	regs.eax = 0x4f01;
	regs.ecx = mode;
	regs.es = (u_int32_t)(mem - LRMI_base_addr()) >> 4;
	regs.edi = (u_int32_t)(mem - LRMI_base_addr()) & 0x0f;

	/* Do it. */
	iopl(3);
	ioperm(0, 0x400, 1);

	if(LRMI_int(0x10, &regs) == 0) {
		LRMI_free_real(mem);
		return NULL;
	}

	/* Check for successful return. */
	if((regs.eax & 0xffff) != 0x004f) {
		LRMI_free_real(mem);
		return NULL;
	}

	/* Get memory for return. */
	ret = malloc(sizeof(struct vbe_mode_info));
	if(ret == NULL) {
		LRMI_free_real(mem);
		return NULL;
	}

	/* Copy the buffer for return. */
	memcpy(ret, mem, sizeof(struct vbe_mode_info));

	/* Clean up and return. */
	LRMI_free_real(mem);
	return ret;
}

/* Get VBE info. */
struct vbe_parent_info *vbe_get_vbe_info()
{
	struct LRMI_regs regs;
	unsigned char *mem;
	struct vbe_parent_info *ret = NULL;
	int i;

	/* Initialize LRMI. */
	if(LRMI_init() == 0) {
		return NULL;
	}

	/* Allocate a chunk of memory. */
	mem = LRMI_alloc_real(sizeof(struct vbe_mode_info));
	if(mem == NULL) {
		return NULL;
	}
	memset(mem, 0, sizeof(struct vbe_mode_info));

	/* Set up registers for the interrupt call. */
	memset(&regs, 0, sizeof(regs));
	regs.eax = 0x4f00;
	regs.es = (u_int32_t)(mem - LRMI_base_addr()) >> 4;
	regs.edi = (u_int32_t)(mem - LRMI_base_addr()) & 0x0f;
	memcpy(mem, "VBE2", 4);

	/* Do it. */
	iopl(3);
	ioperm(0, 0x400, 1);

	if(LRMI_int(0x10, &regs) == 0) {
		LRMI_free_real(mem);
		return NULL;
	}

	/* Check for successful return code. */
	if((regs.eax & 0xffff) != 0x004f) {
		LRMI_free_real(mem);
		return NULL;
	}

	/* Get memory to return the information. */
	ret = malloc(sizeof(struct vbe_parent_info));
	if(ret == NULL) {
		LRMI_free_real(mem);
		return NULL;
	}
	memcpy(&ret->vbe, mem, sizeof(struct vbe_info));

	/* Set up pointers to usable memory. */
	ret->mode_list_list = (u_int16_t*) (LRMI_base_addr() +
                                            (ret->vbe.mode_list_addr.seg << 4) +
					    (ret->vbe.mode_list_addr.ofs));
	ret->oem_name_string = (char*) (LRMI_base_addr() +
                                        (ret->vbe.oem_name_addr.seg << 4) +
					(ret->vbe.oem_name_addr.ofs));

	/* Snip, snip. */
	mem = strdup(ret->oem_name_string); /* leak */
	while(((i = strlen(mem)) > 0) && isspace(mem[i - 1])) {
		mem[i - 1] = '\0';
	}
	ret->oem_name_string = mem;

	/* Set up pointers for VESA 2.0+ strings. */
	if(ret->vbe.version[1] >= 2) {

		/* Vendor name. */
		ret->vendor_name_string = (char*)
			 (LRMI_base_addr() +
                          (ret->vbe.vendor_name_addr.seg << 4)
			+ (ret->vbe.vendor_name_addr.ofs));

		mem = strdup(ret->vendor_name_string); /* leak */
		while(((i = strlen(mem)) > 0) && isspace(mem[i - 1])) {
			mem[i - 1] = '\0';
		}
		ret->vendor_name_string = mem;

		/* Product name. */
		ret->product_name_string = (char*)
			 (LRMI_base_addr() + 
                          (ret->vbe.product_name_addr.seg << 4)
			+ (ret->vbe.product_name_addr.ofs));

		mem = strdup(ret->product_name_string); /* leak */
		while(((i = strlen(mem)) > 0) && isspace(mem[i - 1])) {
			mem[i - 1] = '\0';
		}
		ret->product_name_string = mem;

		/* Product revision. */
		ret->product_revision_string = (char*)
			 (LRMI_base_addr() +
                          (ret->vbe.product_revision_addr.seg << 4)
			+ (ret->vbe.product_revision_addr.ofs));

		mem = strdup(ret->product_revision_string); /* leak */
		while(((i = strlen(mem)) > 0) && isspace(mem[i - 1])) {
			mem[i - 1] = '\0';
		}
		ret->product_revision_string = mem;
	}

	/* Cleanup. */
	LRMI_free_real(mem);
	return ret;
}

/* Check if EDID queries are suorted. */
int get_edid_supported()
{
	struct LRMI_regs regs;
	int ret = 0;

	/* Initialize LRMI. */
	if(LRMI_init() == 0) {
		return 0;
	}

	memset(&regs, 0, sizeof(regs));
	regs.eax = 0x4f15; /* VBE DDC service */
	regs.ebx = 0x0000; /* SERVICE_REPORT_DDC */
        regs.es = 0x3000;
        regs.edi = 0x3000;

	/* Do it. */
	iopl(3);
	ioperm(0, 0x400, 1);

	if(LRMI_int(0x10, &regs) == 0) {
		return 0;
	}

	/* Check for successful return. */
	if((regs.eax & 0xff) == 0x4f) {
		/* Supported. */
		ret = 1;
	} else {
		/* Not supported. */
		ret = 0;
	}

	/* Clean up and return. */
	return ret;
}

/* Get EDID info. */
struct edid1_info *get_edid_info()
{
	struct LRMI_regs regs;
	unsigned char *mem;
	struct edid1_info *ret = NULL;
	u_int16_t man;

	/* Initialize LRMI. */
	if(LRMI_init() == 0) {
		return NULL;
	}

	/* Allocate a chunk of memory. */
	mem = LRMI_alloc_real(sizeof(struct edid1_info));
	if(mem == NULL) {
		return NULL;
	}
	memset(mem, 0, sizeof(struct edid1_info));

	memset(&regs, 0, sizeof(regs));
	regs.eax = 0x4f15;
	regs.ebx = 0x0001;
	regs.es = (u_int32_t)(mem) >> 4;
	regs.edi = (u_int32_t)(mem) & 0x0f;

	/* Do it. */
	iopl(3);
	ioperm(0, 0x400, 1);

	if(LRMI_int(0x10, &regs) == 0) {
		LRMI_free_real(mem);
		return NULL;
	}

#if 0
	/* Check for successful return. */
	if((regs.eax & 0xffff) != 0x004f) {
		LRMI_free_real(mem);
		return NULL;
	}
#elseif
	/* Check for successful return. */
	if((regs.eax & 0xff) != 0x4f) {
		LRMI_free_real(mem);
		return NULL;
	}
#endif

	/* Get memory for return. */
	ret = malloc(sizeof(struct edid1_info));
	if(ret == NULL) {
		LRMI_free_real(mem);
		return NULL;
	}

	/* Copy the buffer for return. */
	memcpy(ret, mem, sizeof(struct edid1_info));

	memcpy(&man, &ret->manufacturer_name, 2);
	man = ntohs(man);
	memcpy(&ret->manufacturer_name, &man, 2);

	LRMI_free_real(mem);
	return ret;
}

/* Figure out what the current video mode is. */
int32_t vbe_get_mode()
{
	struct LRMI_regs regs;
	int32_t ret = -1;

	/* Initialize LRMI. */
	if(LRMI_init() == 0) {
		return -1;
	}

	memset(&regs, 0, sizeof(regs));
	regs.eax = 0x4f03;

	/* Do it. */
	iopl(3);
	ioperm(0, 0x400, 1);

	if(LRMI_int(0x10, &regs) == 0) {
		return -1;
	}

	/* Save the returned value. */
	if((regs.eax & 0xffff) == 0x004f) {
		ret = regs.ebx & 0xffff;
	} else {
		ret = -1;
	}

	/* Clean up and return. */
	return ret;
}

/* Set the video mode. */
void vbe_set_mode(u_int16_t mode)
{
	struct LRMI_regs regs;

	/* Initialize LRMI. */
	if(LRMI_init() == 0) {
		return;
	}

	memset(&regs, 0, sizeof(regs));
	regs.eax = 0x4f02;
	regs.ebx = mode;

	/* Do it. */
	iopl(3);
	ioperm(0, 0x400, 1);
	LRMI_int(0x10, &regs);

	/* Return. */
	return;
}

const void *vbe_save_svga_state()
{
	struct LRMI_regs regs;
	unsigned char *mem;
	u_int16_t block_size;
	void *data;

	/* Initialize LRMI. */
	if(LRMI_init() == 0) {
		return NULL;
	}

	memset(&regs, 0, sizeof(regs));
	regs.eax = 0x4f04;
	regs.ecx = 0xffff;
	regs.edx = 0;

	iopl(3);
	ioperm(0, 0x400, 1);

	if(LRMI_int(0x10, &regs) == 0) {
		return NULL;
	}

	if((regs.eax & 0xff) != 0x4f) {
		fprintf(stderr, "Get SuperVGA Video State not supported.\n");
		return NULL;
	}

	if((regs.eax & 0xffff) != 0x004f) {
		fprintf(stderr, "Get SuperVGA Video State Info failed.\n");
		return NULL;
	}

	block_size = 64 * (regs.ebx & 0xffff);

	/* Allocate a chunk of memory. */
	mem = LRMI_alloc_real(block_size);
	if(mem == NULL) {
		return NULL;
	}
	memset(mem, 0, sizeof(block_size));
	
	memset(&regs, 0, sizeof(regs));
	regs.eax = 0x4f04;
	regs.ecx = 0x000f;
	regs.edx = 0x0001;
	regs.es  = (u_int32_t)(mem) >> 4;
	regs.ebx = (u_int32_t)(mem) & 0x0f;
	memset(mem, 0, block_size);
	iopl(3);
	ioperm(0, 0x400, 1);

	if(LRMI_int(0x10, &regs) == 0) {
		LRMI_free_real(mem);
		return NULL;
	}

	if((regs.eax & 0xffff) != 0x004f) {
		fprintf(stderr, "Get SuperVGA Video State Save failed.\n");
		return NULL;
	}

	data = malloc(block_size);
	if(data == NULL) {
		LRMI_free_real(mem);
		return NULL;
	}

	/* Clean up and return. */
	memcpy(data, mem, block_size);
	LRMI_free_real(mem);
	return data;
}

void vbe_restore_svga_state(const void *state)
{
	struct LRMI_regs regs;
	unsigned char *mem;
	u_int16_t block_size;

	/* Initialize LRMI. */
	if(LRMI_init() == 0) {
		return;
	}

	memset(&regs, 0, sizeof(regs));
	regs.eax = 0x4f04;
	regs.ecx = 0x000f;
	regs.edx = 0;

	/* Find out how much memory we need. */
	iopl(3);
	ioperm(0, 0x400, 1);

	if(LRMI_int(0x10, &regs) == 0) {
		return;
	}

	if((regs.eax & 0xff) != 0x4f) {
		fprintf(stderr, "Get SuperVGA Video State not supported.\n");
		return;
	}

	if((regs.eax & 0xffff) != 0x004f) {
		fprintf(stderr, "Get SuperVGA Video State Info failed.\n");
		return;
	}

	block_size = 64 * (regs.ebx & 0xffff);

	/* Allocate a chunk of memory. */
	mem = LRMI_alloc_real(block_size);
	if(mem == NULL) {
		return;
	}
	memset(mem, 0, sizeof(block_size));

	memset(&regs, 0, sizeof(regs));
	regs.eax = 0x4f04;
	regs.ecx = 0x000f;
	regs.edx = 0x0002;
	regs.es  = 0x2000;
	regs.ebx = 0x0000;
	memcpy(mem, state, block_size);

	iopl(3);
	ioperm(0, 0x400, 1);

	if(LRMI_int(0x10, &regs) == 0) {
		LRMI_free_real(mem);
		return;
	}

	if((regs.eax & 0xffff) != 0x004f) {
		fprintf(stderr, "Get SuperVGA Video State Restore failed.\n");
		return;
	}
}

#endif /* __i386__ */
