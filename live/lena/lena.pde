
#include <SPI.h>
#include <GD.h>

#include "lena.h"

void setup()
{
  GD.begin();
  for (byte y = 0; y < 38; y++)
    GD.copy(RAM_PIC + y * 64, lena_pic + y * 38, 38);
  GD.copy(RAM_CHR, lena_chr, sizeof(lena_chr));
  GD.copy(RAM_PAL, lena_pal, sizeof(lena_pal));
}

void loop()
{
}