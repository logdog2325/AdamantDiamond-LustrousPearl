// The types dw_core.c (include/pearlb2/plat_dw.h) uses, on the Mac (the DS build takes Black 2's types.h, nitro/fx.h)
#ifndef DW_HOST_TYPES_H
#define DW_HOST_TYPES_H
#include <stddef.h>
#include <stdint.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int8_t s8;
typedef int16_t s16;
typedef int32_t s32;
typedef int32_t fx32;
typedef int BOOL;
#define TRUE 1
#define FALSE 0
#define FX32_SHIFT 12
#define FX32_ONE 4096
#define FX32_CONST(x) ((fx32)((x) * 4096))
typedef struct {
    fx32 x, y, z;
} VecFx32;
#endif
