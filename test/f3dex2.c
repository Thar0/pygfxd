#define F3DEX_GBI_2
#include "gbi.h"

Gfx emptyDList[] = {
    gsSPEndDisplayList(),
};

Gfx oneTriDList[] = {
    gsSPVertex(0x42042069, 3, 0),
    gsSP1Triangle(0, 1, 2, 0),
    gsSPEndDisplayList(),
};

Gfx setLights1DList[] = {
    gsSPSetLights1(*(Lightsn *)0x09000000),
};
