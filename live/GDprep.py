import sys
import Image
from array import array
import os
import unittest

def rgb555(r, g, b):
    """
    Return the 15-bit hw representation for 8-bit RGB color (r,g,b)
    """
    return ((r / 8) << 10) + ((g / 8) << 5) + (b / 8)

def rgbpal(imdata):
    # For RGB imdata, return list of (r,g,b) triples and the palette
    li = array('B', imdata).tolist()
    rgbs = zip(li[0::3], li[1::3], li[2::3])
    palette = list(set(rgbs))
    return (rgbs, palette)

def getch(im, x, y):
    """
    Return the 4-color image for the 8x8 character at (x, y) in im.
    if the 8x8 image contains more than 4 colors, quantize it using
    PIL's adaptive palette algorithm
    """

    sub88 = im.crop((x, y, x + 8, y + 8))
    sub88d = sub88.tostring()
    (_, pal) = rgbpal(sub88d)
    if len(pal) > 4:
        return sub88.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=4).convert("RGB")
    else:
        return sub88
    
def binary(imdata):
    # imdata is 8x8x3 RGB character, string of length 192
    # return the pixel data and palette data for it
    assert len(imdata) == (3 * 8 * 8)
    (rgbs, palette) = rgbpal(imdata)
    indices = [palette.index(c) for c in rgbs]
    indices_b = ""
    for i in range(0, len(indices), 4):
        if 0:
            c =   ((indices[i] << 6) +
                   (indices[i + 1] << 4) +
                   (indices[i + 2] << 2) +
                   (indices[i + 3]))
        else:
            lup = [ 0x00, 0x08, 0x80, 0x88 ]
            c = ((lup[indices[i]]) +
                 (lup[indices[i + 1]] >> 1) +
                 (lup[indices[i + 2]] >> 2) +
                 (lup[indices[i + 3]] >> 3));
        indices_b += (chr(c))
    palette = (palette + ([(0,0,0)] * 4))[:4]
    ph = array('H', [rgb555(*p) for p in palette])
    ph.byteswap()
    palette_b = ph.tostring()
    return (indices_b, palette_b)

class Report:
    def __init__(self):
        self.lines = []
    def add(self, msg):
        self.lines.append(msg)
    def get(self):
        return self.lines

def encode(im):
    r = Report()
    preview = Image.new("RGB", im.size)
    charset = {}
    picture = []
    im = im.convert("RGB")
    if ((im.size[0] % 8) != 0) or ((im.size[1] % 8) != 0):
        r.add("Image size is %d x %d, but must be multiple of 8" % im.size)
        return (r, {})
    for y in range(0, im.size[1], 8):
        for x in range(0, im.size[0], 8):
            iglyph = getch(im, x, y)
            preview.paste(iglyph, (x, y))
            glyph = iglyph.tostring()
            if not glyph in charset:
                charset[glyph] = len(charset)
            picture.append(charset[glyph])
    r.add('Image uses %d unique characters' % len(charset))
    if len(charset) > 256:
        r.add("Maximum number of characters is 256.  Cannot encode.")
        return (r, {})
    else:
        picd = array('B', picture)
        cd = array('B', [0] * 16 * len(charset))
        pd = array('B', [0] * 8 * len(charset))
        for d,i in charset.items():
            for y in range(8):
                (char, pal) = binary(d)
                cd[16 * i:16 * (i+1)] = array('B', char)
                pd[8 * i:8 * (i+1)] = array('B', pal)
        binset = (picd, cd, pd)
        return (r, {'preview': preview, 'binset' : binset})

def dump(hh, name, data):
    print >>hh, "static PROGMEM prog_uchar %s[] = {" % name
    bb = array('B', data.tostring())
    for i in range(0, len(bb), 16):
        if (i & 0xff) == 0:
            print >>hh
        for c in bb[i:i+16]:
            print >>hh, "0x%02x, " % c,
        print >>hh
    print >>hh, "};"

def main(filename):
    im = Image.open(filename).convert("RGB")
    (picdata, chrdata, paldata) = encode(im)
    open(filename + ".pic", "w").write(picdata.tostring())
    open(filename + ".chr", "w").write(chrdata.tostring())
    open(filename + ".pal", "w").write(paldata.tostring())

class TestEncoder(unittest.TestCase):
    def test_asteroid(self):
        im = Image.open("asteroid.png").convert("RGB")
        (report, res) = encode(im)
        (picdata, chrdata, paldata) = res['binset']
        print res['preview']
        print report.get()

if __name__ == "__main__":
    unittest.main()
