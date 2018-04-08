/*
 * lunix-sensors.c
 *
 * Sensor buffer management
 * for Lunix:TNG
 *
 * Vangelis Koukis <vkoukis@cslab.ece.ntua.gr>
 *
 */

#include <linux/mm.h>
#include <linux/fs.h>
#include <linux/init.h>
#include <linux/list.h>
#include <linux/poll.h>
#include <linux/slab.h>
#include <linux/sched.h>
#include <linux/ioctl.h>
#include <linux/types.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/mmzone.h>
#include <linux/vmalloc.h>
#include <linux/spinlock.h>

#include "lunix.h"

/*
 * Initialization and destruction of sensor structures
 * Invoked from: lunix-module.c
 *      module_init(lunix_module_init);
 *      module_exit(lunix_module_cleanup);
 */
int lunix_sensor_init(struct lunix_sensor_struct *s)
{
	int i;
	int ret;
	unsigned long p;

	/*
	 * Initialize structure fields
	 */
	spin_lock_init(&s->lock);           /* linux/spinlock.h */
	init_waitqueue_head(&s->wq);

	/*
	 * Allocate one page per measurement buffer
	 */
	for (i = 0; i < N_LUNIX_MSR; i++)
		s->msr_data[i] = NULL;

	for (i = 0; i < N_LUNIX_MSR; i++) {
		p = get_zeroed_page(GFP_KERNEL);
		if (!p) {
			ret = -ENOMEM;
			goto out;
		}
		s->msr_data[i] = (struct lunix_msr_data_struct *)p;
		s->msr_data[i]->magic = LUNIX_MSR_MAGIC;
	}

	ret = 0;
out:
	return ret;
}

/*
 * Destroy universe,
 * deallocate all memory and free resources
 * when `modprobe -r <lunix_driver>`
 */
void lunix_sensor_destroy(struct lunix_sensor_struct *s)
{
	int i;

	for (i = 0; i < N_LUNIX_MSR; i++) {
		if (s->msr_data[i])
			free_page((unsigned long)s->msr_data[i]);
	}
}

void lunix_sensor_update(struct lunix_sensor_struct *s,
	uint16_t batt, uint16_t temp, uint16_t light)
{
    /*
     * spinlock: - should be small and fast
     *           - atomic update
     */
	spin_lock(&s->lock);
	
	/* Critical Section:
	 * Update the raw values and the relevant timestamps.
	 */
	s->msr_data[BATT]->values[0] = batt;    /* battery measurements */
	s->msr_data[TEMP]->values[0] = temp;    /* temperature measurements */
	s->msr_data[LIGHT]->values[0] = light;  /* light measurements */

	s->msr_data[BATT]->magic = s->msr_data[TEMP]->magic = s->msr_data[LIGHT]->magic = LUNIX_MSR_MAGIC;  /* LUNIX_MSR_MAGIC =>> 0xFOODFOOD */
	s->msr_data[BATT]->last_update = s->msr_data[TEMP]->last_update = s->msr_data[LIGHT]->last_update = get_seconds();
	
	spin_unlock(&s->lock);

	/*
	 * And wake up any sleepers who may be waiting on
	 * fresh data from this sensor (stored in spinlock's `s` waitqueue `wq`.
	 */
	wake_up_interruptible(&s->wq);
}
