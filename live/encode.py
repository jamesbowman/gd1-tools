import Image
import json
import StringIO
import cgi
import array
import string
import zipfile

from Cheetah.Template import Template
import gameduino.prep as gdprep
from gameduino.compress import Codec
import gameduino
import gameduino.sim as gdsim

common = """
#include <SPI.h>
#include <GD.h>

#include "${name}.h"

void setup()
{
  GD.begin();
"""


def showbg(dstdir, im, pic_chr_pal, name, compress):
    (picdata,chrdata,paldata) = pic_chr_pal
    # tilecode: mapping from tilecoords to code
    tilecode = {}
    stride = im.size[0] / 8
    for i in range(im.size[0] / 8):
      for j in range(im.size[1] / 8):
        tilecode["%s,%s" % (i,j)] = picdata[i + (j * stride)]

    # codetiles: mapping from code to all tiles w that code
    codetiles = [[] for i in range(256)]
    for i in range(im.size[0] / 8):
      for j in range(im.size[1] / 8):
        code = picdata[i + (j * stride)]
        codetiles[code].append((i,j))

    fullscreen = (im.size == (512, 512))

    nbytes = len(chrdata) / 16

    hh = StringIO.StringIO()
    if compress:
        cc = Codec(b_off = 9, b_len = 3)
        if fullscreen:
            picdata = cc.toarray(picdata.tostring())
        chrdata = cc.toarray(chrdata.tostring())
        paldata = cc.toarray(paldata.tostring())

    gdprep.dump(hh, "%s_pic" % name, picdata)
    gdprep.dump(hh, "%s_chr" % name, chrdata)
    gdprep.dump(hh, "%s_pal" % name, paldata)


    tmpl = common
    if fullscreen and compress:
      tmpl += "  GD.uncompress(RAM_PIC, ${name}_pic);\n"
    else:
      tmpl += """  for (byte y = 0; y < %d; y++)
    GD.copy(RAM_PIC + y * 64, ${name}_pic + y * %d, %d);
""" % (im.size[1] / 8, im.size[0] / 8, im.size[0] / 8)
    if compress:
        tmpl += "  GD.uncompress(RAM_CHR, ${name}_chr);\n"
        tmpl += "  GD.uncompress(RAM_PAL, ${name}_pal);\n"
    else:
        tmpl += "  GD.copy(RAM_CHR, ${name}_chr, sizeof(${name}_chr));\n"
        tmpl += "  GD.copy(RAM_PAL, ${name}_pal, sizeof(${name}_pal));\n"

    tmpl += """}

void loop()
{
}"""

    ploader = string.Template(tmpl).substitute({'name': name})

    nameSpace = {
        'name' : name,
        'width' : im.size[0],
        'height' : im.size[1],
        'nchars' : nbytes,
        'nbytes' : len(picdata) + len(chrdata) + len(paldata),
        'tilecode' : json.dumps(tilecode),
        'codetiles' : json.dumps(codetiles),
        'pagecode': open("bgcomplete.js").read(),
        'pde' : cgi.escape(ploader),
        'h': hh.getvalue(),
    }
    ct = Template(open("bgcomplete.html").read(), searchList=[nameSpace])
    open("%s/index.html" % dstdir, "w").write(str(ct))

    z = zipfile.ZipFile(dstdir + "/" + name + ".zip", "w")
    z.writestr("%s/%s.pde" % (name, name), ploader)
    z.writestr("%s/%s.h" % (name, name), hh.getvalue())
    z.close()

def bgencode(dstdir, im, name, compress):
    def bgproblem(problem):
        nameSpace = {'problem' : problem}
        ct = Template(open("bgerror.html").read(), searchList=[nameSpace])
        open("%s/index.html" % dstdir, "w").write(str(ct))

    badwidth = (im.size[0] % 8) != 0
    badheight = (im.size[1] % 8) != 0
    suggest = " -- resize to %d wide by %d high?" % ((im.size[0] + 7) & ~7, (im.size[1] + 7) & ~7)
    if badwidth and badheight:
        return bgproblem("The image width and height must be a multiples of 8" + suggest)
    if badwidth:
        return bgproblem("The image width must be a multiple of 8" + suggest)
    if badheight:
        return bgproblem("The image height must be a multiple of 8" + suggest)

    try:
        (picdata,chrdata,paldata) = gdprep.encode(im)
    except OverflowError:
        return bgproblem("The source image uses more than 256 unique characters")
        
    im.save("%s/%s.png" % (dstdir, name))
    showbg(dstdir, im, (picdata,chrdata,paldata), name, compress)

def lossyencode(dstdir, im, name, tgt):
    import xmlrpclib
    s = xmlrpclib.ServerProxy('http://192.168.0.118:8000')
    sz = im.size
    if sz[0] > 400:
        sz = (400, sz[1] * 400 / sz[0])
    if sz[1] > 296:
        sz = (sz[0] * 296 / sz[1], 296)
    def near8(x):
        return 8 * int(round(x / 8.))
    sz = (near8(sz[0]), near8(sz[1]))
    im = im.resize(sz, Image.BILINEAR).convert("RGB")
    sd = im.tostring()
    picd,chrd,pald = [array.array('B', x.data) for x in s.encode_simple(im.size, xmlrpclib.Binary(sd), tgt)]
        
    gd = gdsim.Gameduino()
    gd.fill(gameduino.RAM_PIC, 0xff, 64 * 64)
    ls = im.size[0] / 8
    for y in range(im.size[1] / 8):
        gd.wrstr(64 * y + gameduino.RAM_PIC, picd[ls*y:ls*y+ls])
    gd.wrstr(gameduino.RAM_CHR, chrd)
    gd.wrstr(gameduino.RAM_PAL, pald)
    gd.im().save("%s/%s.png" % (dstdir, name))

    showbg(dstdir, im, (picd,chrd,pald), name, False)

def spencode(dstdir, im, name, compress, size, palette):
    def spproblem(problem):
        nameSpace = {'problem' : problem}
        ct = Template(open("sperror.html").read(), searchList=[nameSpace])
        open("%s/index.html" % dstdir, "w").write(str(ct))

    sprites = []
    for y in range(0, im.size[1], size[1]):
        for x in range(0, im.size[0], size[0]):
            sprites.append((x, y))
    hh = StringIO.StringIO()
    ir = gdprep.ImageRAM(hh)
    if '256' in palette:
        ncol = 256
    elif '16' in palette:
        ncol = 16
    else:
        ncol = 4
    im = im.convert("RGBA")
    imp = gdprep.palettize(im, ncol)
    imp.convert("RGBA").save("%s/paletted.png" % dstdir)
    try:
        ir.addsprites(name, size, imp, eval("gdprep.%s" % palette), center=(size[0]/2,size[1]/2))
    except OverflowError:
        return spproblem("The sprite sheet uses too much memory.  Some suggestions: use the smallest palette possible; make sure you have set transparency in the source image.")
        
    if compress:
        cc = Codec(b_off = 9, b_len = 3)
        sprimg = cc.toarray(ir.used().tostring())
    else:
        sprimg = ir.used()
        
    gdprep.dump(hh, name + "_sprimg", sprimg)
    gdprep.dump(hh, name + "_sprpal", gdprep.getpal(imp))
    def gencode():
        palram = {
            "PALETTE256A" : "RAM_SPRPAL",
            "PALETTE256B" : "RAM_SPRPAL + 512",
            "PALETTE256C" : "RAM_SPRPAL + 1024",
            "PALETTE256D" : "RAM_SPRPAL + 1536"};
        yield common
        pram = palram.get(palette, palette)
        yield "  GD.copy(%s, ${name}_sprpal, sizeof(${name}_sprpal));" % pram
        if compress:
            yield "  GD.uncompress(RAM_SPRIMG, ${name}_sprimg);";
        else:
            yield "  GD.copy(RAM_SPRIMG, ${name}_sprimg, sizeof(${name}_sprimg));"
        yield "";
        yield "  // For show, randomly scatter the frames on the screen";
        yield "  GD.__wstartspr(0);"
        yield "  for (int anim = 0; anim < %s_FRAMES; anim++)" % name.upper()
        yield "    draw_${name}(random(400), random(300), anim, 0);"
        yield "  GD.__end();"
        yield "}"
        yield ""
        yield "void loop()"
        yield "{"
        yield "}"

    ploader = "\n".join(list(gencode())).replace("${name}", name)
    nameSpace = {
        'name' : name,
        'sprites' : sprites,
        'width' : size[0],
        'height' : size[1],
        'nbytes' : len(sprimg),
        'pagecode': 'sprites=' + json.dumps(sprites) + ';' + open("spcomplete.js").read(),
        'pde' : cgi.escape(ploader),
        'h': hh.getvalue(),
    }

    ct = Template(open("spcomplete.html").read(), searchList=[nameSpace])
    open("%s/index.html" % dstdir, "w").write(str(ct))

    z = zipfile.ZipFile(dstdir + "/" + name + ".zip", "w")
    z.writestr("%s/%s.pde" % (name, name), ploader)
    z.writestr("%s/%s.h" % (name, name), hh.getvalue())
    z.close()

def bgfront():
    ct = Template(open("bgfront.html").read())
    return str(ct)

def spfront():
    ct = Template(open("spfront.html").read())
    return str(ct)

def lossyfront():
    ct = Template(open("lossyfront.html").read())
    return str(ct)

# bgencode("silly", Image.open("froggerbg.png"), "froggerbg", False)
# spencode("silly", Image.open("sprites.png"), "sprite", True, (16,16), "PALETTE16A")
# ct = Template(open("spfront.html").read())
# open("index.html", "w").write(str(ct))
