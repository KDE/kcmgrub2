#include <sys/types.h>
#include <sys/mman.h>
#include <netinet/in.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>
#include <limits.h>
#include <ctype.h>
#include "vesamode.h"
#include "common.h"

/* Just read ranges from the EDID. */
void get_edid_ranges(unsigned char *hmin, unsigned char *hmax,
			unsigned char *vmin, unsigned char *vmax)
{
	struct edid1_info *edid;
	struct edid_monitor_descriptor *monitor;
	int i;

	*hmin = *hmax = *vmin = *vmax = 0;

	if((edid = get_edid_info()) == NULL) {
		return;
	}

	for(i = 0; i < 4; i++) {
		monitor = &edid->monitor_details.monitor_descriptor[i];
		if(monitor->type == edid_monitor_descriptor_range) {
			*hmin = monitor->data.range_data.horizontal_min;
			*hmax = monitor->data.range_data.horizontal_max;
			*vmin = monitor->data.range_data.vertical_min;
			*vmax = monitor->data.range_data.vertical_max;
		}
	}
}

static int compare_modelines(const void *m1, const void *m2)
{
	const struct modeline *M1 = (const struct modeline*) m1;
	const struct modeline *M2 = (const struct modeline*) m2;
	if(M1->width < M2->width) return -1;
	if(M1->width > M2->width) return 1;
	return 0;
}

struct modeline *get_edid_modelines()
{
	struct edid1_info *edid;
	struct modeline *ret;
	char buf[LINE_MAX];
	int modeline_count = 0, j;
	unsigned int i;

	if((edid = get_edid_info()) == NULL) {
		return NULL;
	}

	memcpy(buf, &edid->established_timings,
	       sizeof(edid->established_timings));
	for(i = 0; i < (8 * sizeof(edid->established_timings)); i++) {
		if(buf[i / 8] & (1 << (i % 8))) {
			modeline_count++;
		}
	}

	/* Count the number of standard timings. */
	for(i = 0; i < 8; i++) {
		int x, v;
		x = edid->standard_timing[i].xresolution;
		v = edid->standard_timing[i].vfreq;
		if(((edid->standard_timing[i].xresolution & 0x01) != x) &&
		   ((edid->standard_timing[i].vfreq & 0x01) != v)) {
			modeline_count++;
		}
	}

	ret = malloc(sizeof(struct modeline) * (modeline_count + 1));
	if(ret == NULL) {
		return NULL;
	}
	memset(ret, 0, sizeof(struct modeline) * (modeline_count + 1));

	modeline_count = 0;

	/* Fill out established timings. */
	if(edid->established_timings.timing_720x400_70) {
		ret[modeline_count].width = 720;
		ret[modeline_count].height = 400;
		ret[modeline_count].refresh = 70;
		modeline_count++;
	}
	if(edid->established_timings.timing_720x400_88) {
		ret[modeline_count].width = 720;
		ret[modeline_count].height = 400;
		ret[modeline_count].refresh = 88;
		modeline_count++;
	}
	if(edid->established_timings.timing_640x480_60) {
		ret[modeline_count].width = 640;
		ret[modeline_count].height = 480;
		ret[modeline_count].refresh = 60;
		modeline_count++;
	}
	if(edid->established_timings.timing_640x480_67) {
		ret[modeline_count].width = 640;
		ret[modeline_count].height = 480;
		ret[modeline_count].refresh = 67;
		modeline_count++;
	}
	if(edid->established_timings.timing_640x480_72) {
		ret[modeline_count].width = 640;
		ret[modeline_count].height = 480;
		ret[modeline_count].refresh = 72;
		modeline_count++;
	}
	if(edid->established_timings.timing_640x480_75) {
		ret[modeline_count].width = 640;
		ret[modeline_count].height = 480;
		ret[modeline_count].refresh = 75;
		modeline_count++;
	}
	if(edid->established_timings.timing_800x600_56) {
		ret[modeline_count].width = 800;
		ret[modeline_count].height = 600;
		ret[modeline_count].refresh = 56;
		modeline_count++;
	}
	if(edid->established_timings.timing_800x600_60) {
		ret[modeline_count].width = 800;
		ret[modeline_count].height = 600;
		ret[modeline_count].refresh = 60;
		modeline_count++;
	}
	if(edid->established_timings.timing_800x600_72) {
		ret[modeline_count].width = 800;
		ret[modeline_count].height = 600;
		ret[modeline_count].refresh = 72;
		modeline_count++;
	}
	if(edid->established_timings.timing_800x600_75) {
		ret[modeline_count].width = 800;
		ret[modeline_count].height = 600;
		ret[modeline_count].refresh = 75;
		modeline_count++;
	}
	if(edid->established_timings.timing_832x624_75) {
		ret[modeline_count].width = 832;
		ret[modeline_count].height = 624;
		ret[modeline_count].refresh = 75;
		modeline_count++;
	}
	if(edid->established_timings.timing_1024x768_87i) {
		ret[modeline_count].width = 1024;
		ret[modeline_count].height = 768;
		ret[modeline_count].refresh = 87;
		ret[modeline_count].interlaced = 1;
		modeline_count++;
	}
	if(edid->established_timings.timing_1024x768_60){
		ret[modeline_count].width = 1024;
		ret[modeline_count].height = 768;
		ret[modeline_count].refresh = 60;
		modeline_count++;
	}
	if(edid->established_timings.timing_1024x768_70){
		ret[modeline_count].width = 1024;
		ret[modeline_count].height = 768;
		ret[modeline_count].refresh = 70;
		modeline_count++;
	}
	if(edid->established_timings.timing_1024x768_75){
		ret[modeline_count].width = 1024;
		ret[modeline_count].height = 768;
		ret[modeline_count].refresh = 75;
		modeline_count++;
	}
	if(edid->established_timings.timing_1280x1024_75) {
		ret[modeline_count].width = 1280;
		ret[modeline_count].height = 1024;
		ret[modeline_count].refresh = 75;
		modeline_count++;
	}

	/* Add in standard timings. */
	for(i = 0; i < 8; i++) {
		float aspect = 1;
		int x, v;
		x = edid->standard_timing[i].xresolution;
		v = edid->standard_timing[i].vfreq;
		if(((edid->standard_timing[i].xresolution & 0x01) != x) &&
		   ((edid->standard_timing[i].vfreq & 0x01) != v)) {
			switch(edid->standard_timing[i].aspect) {
				case aspect_75: aspect = 0.7500; break;
				case aspect_8: aspect = 0.8000; break;
				case aspect_5625: aspect = 0.5625; break;
				default: aspect = 1; break;
			}
			x = (edid->standard_timing[i].xresolution + 31) * 8;
			ret[modeline_count].width = x;
			ret[modeline_count].height = x * aspect;
			ret[modeline_count].refresh =
				edid->standard_timing[i].vfreq + 60;
			modeline_count++;
		}
	}

	/* Now tack on any matching modelines. */
	for(i = 0; ret[i].refresh != 0; i++) {
		struct vesa_timing_t *t = NULL;
		for(j = 0; known_vesa_timings[j].refresh != 0; j++) {
			t = &known_vesa_timings[j];
			if(ret[i].width == t->x)
			if(ret[i].height == t->y)
			if(ret[i].refresh == t->refresh) {
				snprintf(buf, sizeof(buf),
					 "ModeLine \"%dx%d\"\t%6.2f "
					 "%4d %4d %4d %4d %4d %4d %4d %4d %s %s"
					 , t->x, t->y, t->dotclock,
					 t->timings[0],
					 t->timings[0] + t->timings[1],
					 t->timings[0] + t->timings[1] +
					 t->timings[2],
					 t->timings[0] + t->timings[1] +
					 t->timings[2] + t->timings[3],
					 t->timings[4],
					 t->timings[4] + t->timings[5],
					 t->timings[4] + t->timings[5] +
					 t->timings[6],
					 t->timings[4] + t->timings[5] +
					 t->timings[6] + t->timings[7],
					 t->hsync == hsync_pos ?
					 "+hsync" : "-hsync",
					 t->vsync == vsync_pos ?
					 "+vsync" : "-vsync");
				ret[i].modeline = strdup(buf);
				ret[i].hfreq = t->hfreq;
				ret[i].vfreq = t->vfreq;
			}
		}
	}

	modeline_count = 0;
	for(i = 0; ret[i].refresh != 0; i++) {
		modeline_count++;
	}
	qsort(ret, modeline_count, sizeof(ret[0]), compare_modelines);

	return ret;
}
