/*
 * lunix-chrdev.c
 *
 * Implementation of character devices
 * for Lunix:TNG
 *
 * Edited:
 * Michalis Papadopoullos
 * 03114702
 *
 */

#include <linux/mm.h>
#include <linux/fs.h>
#include <linux/init.h>
#include <linux/list.h>
#include <linux/cdev.h>
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
#include "lunix-chrdev.h"
#include "lunix-tables.h"

#define LUNIX_DRIVER_NAME "lunixTNG"

/*
 * Global data
 */

long *lkpTables[] = { lookup_voltage, lookup_temperature, lookup_light };

/* character device */
struct cdev lunix_chrdev_cdev;		/* linux/cdev.h */


/*
 * source: https://lwn.net/Articles/195805/
 * =========================================
 The newer interface breaks down char device registration into two distinct steps: allocation of a range of device numbers, and association of specific devices with those numbers. The allocation phase is handled with either of:

 int register_chrdev_region(dev_t first, unsigned int count,
 const char *name);
 int alloc_chrdev_region(dev_t *first, unsigned int firstminor,
 unsigned int count, char *name);

 The first form will allocate count minor numbers, starting with the major/minor pair found in first, and remembering name with all of them.
 The second form is intended for use when the desired major number is not known ahead of time;
 it will allocate a major number, then allocate count minor numbers, starting at firstminor. The beginning of the allocated number range will be returned in first.
 The return value will be zero on success or a negative error code on failure.
 */

/* TODO
 * Just a quick [unlocked] check to see if the cached
 * chrdev state needs to be updated from sensor measurements.
 */
static int lunix_chrdev_state_needs_refresh(struct lunix_chrdev_state_struct *state)
{
	struct lunix_sensor_struct *sensor;

	WARN_ON ( !(sensor = state->sensor) );
	/* ?
	 * WHAT IS THIS
	 */

	/*
	 * if last_update > timestamp =>> refresh = 1
	 */
	return sensor->msr_data[state->type]->last_update > state->buf_timestamp;
}

/* TODO:
 * Updates the cached state of a character device
 * based on sensor data. Must be called with the
 * character device state lock held.
 */
static int lunix_chrdev_state_update(struct lunix_chrdev_state_struct *state)
{
	int ret;

	struct lunix_sensor_struct *sensor;
	unsigned long flags;
	int updated;

	uint32_t _data;
	uint32_t _timestamp;

	long __data;

	long dec, frac;		/* decimal, fractional part */
	unsigned char sign;	/* positive (+), negative (-) */
	
	debug("entering state_update()\n");

	/*
	 * Grab the raw data quickly, hold the
	 * spinlock for as little as possible.
	 */

	/* ? =>> What should we use?
	 * down_interruptible ?
	 * spin_lock_irqsave  ?
	 */
	spin_lock_irqsave(&sensor->lock, flags);
	/* ========== Critical Section */

	/* ? */
	/* Why use spinlocks? See LDD3, p. 119 */

	/*
	 * Any new data available?
	 */
	if ((updated = lunix_chrdev_state_needs_refresh(state))) {
		/* grab data ? WHAT IS STORED IN VALUES[] ? */
		_data = sensor->msr_data[state->type]->values[0];
		_timestamp = sensor->msr_data[state->type]->last_update;
	}

	/* ========================================== */
	spin_unlock_irqrestore(&sensor->lock, flags);

	/* ? */

	/*
	 * Now we can take our time to format them,
	 * holding only the private state semaphore
	 */
	ret = 0;
	if (updated) {
		__data = lkpTables[state->type][_data];

		switch (state->mode) {
			case RAW:
				state->buf_data[0] = _data;
				state->buf_data[1] = '\0';
				state->buf_lim = 1;
				break;
				/* RAW */
			case COOKED:
				sign = (__data >= 0) ? '+' : '-';
			 	dec = __data / 1000;
				frac = __data % 1000;

				/* give floating point representation */
				snprintf(state->buf_data, LUNIX_CHRDEV_BUFSZ, "%c%ld.%ld\n", sign, dec, frac);
				state->buf_lim = strnlen(state->buf_data, LUNIX_CHRDEV_BUFSZ);

				/* ensure null terminated strings */
				state->buf_data[state->buf_lim] = '\0';
				break;
				/* COOKED */
			default:
				debug("Unexpected error @ %d\n", __LINE__);
				ret = -EINVAL;
				goto out;
				break;
		}

		/* set corresponding timestamp */
		state->buf_timestamp = _timestamp;
		goto out;
	}
	else if (state->buf_lim > 0) {
		/*
		 * No new data found
		 * although, buffer is not EMPTY !!
		 */
		ret = -EAGAIN;
		goto out;
	}
	else {
		/* Internal Error
		 * -ERESTARTSYS is connected to the concept of a restartable system call.
		 * A restartable system call is one that can be transparently re-executed by the kernel when there is some interruption.
		 */
		ret = -ERESTARTSYS;
		goto out;
	}

out:
	debug("leaving update(), with ret = %d\n", ret);
	return ret;
}

/*************************************
 * Implementation of file operations
 * for the Lunix character device
 *************************************/
// TODO
static int lunix_chrdev_open(struct inode *inode, struct file *filp)
{
	/* Declarations */
	int ret;

	/* pvt state of device */
	struct lunix_chrdev_state_struct *state;

	/* get minor number */
	dev_t _minor_ = iminor(inode);

	/* device type */
	int type = _minor_ & 0xf;

	/* lookup tables */

	// enum lunix_msr_enum { BATT = 0, TEMP, LIGHT, N_LUNIX_MSR };
	if (type >= N_LUNIX_MSR) {
		ret = -ENODEV;  /* NO SUCH DEVICE */
		goto out;
	}

	debug("entering open()\n");
	ret = -ENODEV;
	if ((ret = nonseekable_open(inode, filp)) < 0) {
		goto out;
	}

	/*
	 * Associate this open file with the relevant sensor based on
	 * the minor number of the device node [/dev/sensor<NO>-<TYPE>]
	 */

	/* Allocate a new Lunix character device private state structure *
	 * * Consider using vmalloc()
	 */
	state = kmalloc(sizeof(struct lunix_chrdev_state_struct), GFP_KERNEL);
	if (!state) {
		debug("[var:state] =>> allocation failed");
		ret = -ENOMEM;
		goto out;
	}


	state->type = type;
	state->sensor = &lunix_sensors[_minor_ >> 3];
	state->buf_lim = /*?*/0;

	/* process raw data =>> COOKED */
	state->mode = COOKED;

	/* initialize semaphore =>> mutex */
	sema_init(&state->lock, 1);

	/* preserve state information across syscalls =>> needs to be freed */
	filp->private_data = (void *)state;

out:

	debug("leaving open(), with ret = %d\n", ret);
	return ret;
}

// TODO
static int lunix_chrdev_release(struct inode *inode, struct file *filp)
{
	/*
	 * Deallocate all resources
	 */

	kfree(filp->private_data);  // (struct lunix_chrdev_state_struct *)
	filp->private_data = NULL;

	return 0;
}

// TODO
static long lunix_chrdev_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
	/* Why? */
	return -EINVAL;
}

// TODO
/*      - copy reference from filp
 *      - read up to cnt bytes of data
 *      - save data into buffer
 *      - ?
 */
static ssize_t lunix_chrdev_read(struct file *filp, char __user *usrbuf, size_t cnt, loff_t *f_pos)
{
	ssize_t ret;
	size_t  remaining_data;
	size_t  rfsize;

	struct lunix_sensor_struct *sensor;
	struct lunix_chrdev_state_struct *state;

	// restore =>> filp->private_data = state [`state` from open()]
	state = filp->private_data;
	WARN_ON(!state);

	sensor = state->sensor;
	WARN_ON(!sensor);

	debug("entering read()\n");

	/* Lock? */
	if (    /* !(mutex_is_locked(&state->lock)) && */
		/* mutex_lock_interruptible(&sensor->lock) */
		down_interruptible(&state->lock)) { /* if not locked, try acquire the lock */
		
		/* mutex_lock_interruptible(struct mutex *lock):
		   Lock the mutex like mutex_lock, and return 0 if the mutex has been acquired 
		   or sleep until the mutex becomes available.
		   If a signal arrives while waiting for the lock then this function returns -EINTR. 
		*/		

		ret = -EINTR; /* if lock() interrupted */
		goto out;   /* unable to lock the mutex */
	}

	/*
	 * If the cached character device state needs to be
	 * updated by actual sensor data (i.e. we need to report
	 * on a "fresh" measurement, do so
	 */
	if (*f_pos == 0) {  /* we are at the beginning position */
		while (lunix_chrdev_state_update(state) == -EAGAIN) {
			mutex_unlock(&state->lock);

			/* The process needs to sleep =>> semaphore lock */
			/* See LDD3, page 153 for a hint */

			if (filp->f_flags & O_NONBLOCK) { /* NON BLOCKING */
				ret = -ERESTARTSYS;
				goto out;
			}

			/*  The process is put to sleep (TASK_INTERRUPTIBLE) until the condition evaluates to true or a signal is received. The condition is checked each time the waitqueue wq is woken up.
			    The function will return -ERESTARTSYS if it was interrupted by a signal and 0 if condition evaluated to true.
			 */
			if( wait_event_interruptible(sensor->wq, lunix_chrdev_state_needs_refresh(state)) ) {
				ret = -ERESTARTSYS;
				goto out;
			}

			/* make sure mutex is unlocked before trying to acquire */
			if (!mutex_is_locked(&sensor->lock) && mutex_lock_interruptible(&sensor->lock)) {

			}
		}
	}

	/* total_size - current_position = remaining_data */
	remaining_data = state->buf_lim - *f_pos;

	/* End of file */
	if (remaining_data <= 0) { // EOF
		printk(KERN_DEBUG "Reached EOF\n");
		return -ENOSPC; /* No space left on device */
	}

	/* Determine the number of cached bytes to copy to userspace */

	rfsize = (*f_pos + cnt >= state->buf_lim) ? state->buf_lim - *f_pos : cnt;

	/* Returns number of bytes that could not be copied.
	 * On success, this will be zero.
	 */
	if ((remaining_data = copy_to_user(usrbuf, state->buf_data + *f_pos, rfsize)) != 0) { // partial copy
		ret = -EFAULT;
		goto unlock;
	}

	/*
	 * On success, remaining_data = 0
	 * and therefore |rfsize| bytes of data have been copied
	 */
	*f_pos += rfsize;

	/* return number of bytes succesfully read */
	ret = rfsize;

	/* Auto-rewind on EOF mode? */
	if (*f_pos >= state->buf_lim) {
		debug("EOF: auto-rewind\n");
		*f_pos = 0;
	}

unlock: /* Unlock? */
	if (mutex_is_locked(&sensor->lock)) { /* make sure mutex is locked before trying to unlock */
		mutex_unlock(&sensor->lock);
	}
out:
	return ret;
}

// TODO
static int lunix_chrdev_mmap(struct file *filp, struct vm_area_struct *vma)
{
	return -EINVAL;
}

/* TODO
 *      - channge current position of buffer
 */
static int lunix_chrdev_llseek(struct file *filp, loff_t offset, int orig)
{
	loff_t ret = 0;
	switch (orig) {
		case 0:
			if (offset < 0) {
				ret = -EINVAL;
				break;
			}
			if((unsigned int)offset > LUNIX_CHRDEV_BUFSZ) {
				ret = -EINVAL;
				break;
			}
			filp->f_pos = (loff_t)offset;
			ret = filp->f_pos;
			break;

		case 1:
			if((filp->f_pos + offset) > LUNIX_CHRDEV_BUFSZ) { // overflow ?
				ret = -EINVAL;
				break;
			}
			if((filp->f_pos + offset) < 0) { // underflow ?
				ret = -EINVAL;
				break;
			}
			filp->f_pos += offset;
			ret = filp->f_pos;
			break;

		default:
			ret = -EINVAL;
			break;
	}

	return ret;
}

// TODO
static struct file_operations lunix_chrdev_fops = 
{   .owner          = THIS_MODULE,
	.open           = lunix_chrdev_open, 	/* register device */
	.release        = lunix_chrdev_release,	/* destroy device */
	.read           = lunix_chrdev_read,	/* get data */
	.unlocked_ioctl = lunix_chrdev_ioctl,	/* TODO */
	.mmap           = lunix_chrdev_mmap,	/* TODO */
	.llseek         = lunix_chrdev_llseek,	/* change position */
};

int lunix_chrdev_init(void)
{
	/*
	 * Register the character device with the kernel, asking for
	 * a range of minor numbers (number of sensors * 8 measurements / sensor)
	 * beginning with LINUX_CHRDEV_MAJOR:0
	 */
	int ret;
	dev_t dev_no; /* device number */
	unsigned int lunix_minor_cnt = lunix_sensor_cnt << 3;

	debug("init: initializing character device\n");

	/* register cdev */
	cdev_init(&lunix_chrdev_cdev, &lunix_chrdev_fops);      /* void cdev_init(struct cdev *cdev, const struct file_operations *fops);       */
	lunix_chrdev_cdev.owner = THIS_MODULE;                  /* The owner field of the structure should be initialized to THIS_MODULE to protect against ill-advised module unloads while the device is active. */

	/* setup device */
	dev_no = MKDEV(LUNIX_CHRDEV_MAJOR, 0);                  /* #define MKDEV(ma,mi)	(((ma) << MINORBITS) | (mi)) */


	/* TODO
	 * Registering cdev:
	 * int cdev_add(struct cdev *cdev, dev_t first, unsigned int count);
	 * This function will add cdev to the system.
	 * It will service operations for the count device numbers starting with first; a cdev will often serve a single device number, but it does not have to be that way.
	 * Note that cdev_add() can fail; if the return code is zero, the device has not been added to the system.
	 *
	 ***   After a device number range has been obtained, the device needs to be activated by adding
	 ***   it to the character device database. This requires initializing an instance of struct cdev with
	 ***   cdev_init , followed by a call to cdev_add . The prototypes of the functions are defined as
	 ***   follows:
	 */


	/* void cdev_init(struct cdev *cdev, const struct file_operations *fops); */
	/* int cdev_add(struct cdev *p, dev_t dev, unsigned count); */


	/* register_chrdev_region? */
	/* int register_chrdev_region(dev_t from, unsigned count, const char *name) */
	ret = register_chrdev_region(dev_no, lunix_minor_cnt, LUNIX_DRIVER_NAME);
	if (ret < 0) {
		debug("init: failed to register region, ret = %d\n", ret);
		goto out;
	}
	debug("init: devices registered!\n");

	/* ? */
	/* int cdev_add(struct cdev *cdev, dev_t first, unsigned int count); */
	ret = cdev_add(&lunix_chrdev_cdev, dev_no, lunix_minor_cnt);
	if (ret < 0) {
		debug("failed to add character device\n");
		goto out_with_chrdev_region;
	}
	debug("init: devices added to the system - check /sys/dev/\n");

	debug("init: completed successfully\n");
	return 0;

out_with_chrdev_region:
	/* unregister device in case of error */
	unregister_chrdev_region(dev_no, lunix_minor_cnt);
out:
	return ret;
}

void lunix_chrdev_destroy(void)
{
	dev_t dev_no;
	unsigned int lunix_minor_cnt = lunix_sensor_cnt << 3;

	debug("entering\n");
	dev_no = MKDEV(LUNIX_CHRDEV_MAJOR, 0);
	cdev_del(&lunix_chrdev_cdev);
	/* unregister device */
	unregister_chrdev_region(dev_no, lunix_minor_cnt);
	debug("leaving\n");
}
