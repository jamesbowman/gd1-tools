import xmlrpclib

s = xmlrpclib.ServerProxy('http://192.168.0.118:8000')

import Image
import gameduino
import gameduino.sim as gdsim
import array

im = Image.open("titanic.png")
# (dpic, dchr, dpal) = 
sd = im.tostring()

def preview(imsz,picd,chrd,pald):
    gd = gdsim.Gameduino()
    gd.fill(gameduino.RAM_PIC, 0xff, 64 * 64)
    ls = im.size[0] / 8
    for y in range(im.size[1] / 8):
        gd.wrstr(64 * y + gameduino.RAM_PIC, picd[ls*y:ls*y+ls])
    gd.wrstr(gameduino.RAM_CHR, chrd)
    gd.wrstr(gameduino.RAM_PAL, pald)
    return gd.im()

dpic,dchr, dpal = [x.data for x in s.encode_simple(im.size, xmlrpclib.Binary(sd), 255)]
preview(im.size, dpic,dchr, dpal).save("out.png")
