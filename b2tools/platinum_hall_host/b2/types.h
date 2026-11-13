// The harness's stand-in for the decomp's include/types.h (the same widths; s32 is the DS's signed long, 32 bits)
#ifndef HALL_HOST_B2_TYPES_H
#define HALL_HOST_B2_TYPES_H
#include <stdint.h>
#include <stddef.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int8_t s8;
typedef int16_t s16;
typedef int32_t s32;
typedef float f32;
typedef int BOOL;
#define TRUE 1
#define FALSE 0
#endif
