import unittest
import os
import random
import array

import Image
import encode

def randstr(l):
    return array.array('B', [random.randrange(256) for i in range(l)]).tostring()

class TestBg(unittest.TestCase):
    def setUp(self):
        self.dstdir = "tstout"
        try:
            os.mkdir(self.dstdir)
        except:
            pass

    def xxtest_lossy(self):
        im = Image.open("lena.jpg")
        encode.lossyencode(self.dstdir, im, "lena", 255)

    def test_asteroid(self):
        im = Image.open("asteroid.png")
        for comp in [False, True]:
            encode.bgencode(self.dstdir, im, "asteroid", comp)

    def test_overflow(self):
        im = Image.fromstring("L", (256,256), randstr(256 * 256 * 1))
        encode.bgencode(self.dstdir, im, "overflow", False)

if __name__ == "__main__":
    unittest.main()

