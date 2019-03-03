"""
"""

import os
localDir = os.path.dirname(__file__)
absDir = os.path.join(os.getcwd(), localDir)

import random
import StringIO
import cherrypy
import GDprep

cherrypy.config.update({'server.socket_host': '127.0.0.1',
                        'server.socket_port': 8803,
                                               })

from Cheetah.Template import Template
import Image

ix = Template.compile(file="index.html")
uf = Template.compile(file="uploadform.html")
tc = Template.compile(file="results.html")

class Live:
    def index(self):
        raise cherrypy.HTTPRedirect("/tools/", 301)
        return str(uf())
        return """
        """
    index.exposed = True

    def upload(self, myFile, name):
        im = Image.open(myFile.file)

        (report, results) = GDprep.encode(im)
        t = tc()
        t.report = report.get()
        if 'preview' in results:
            hash = "%08x" % random.getrandbits(32)
            os.mkdir("../site/results/%s" % hash)
            previewfile = hash + "/preview.png"
            results['preview'].save("../site/results/" + previewfile)
            t.preview = "/results/" + previewfile
            (picdata, chrdata, paldata) = results['binset']

            # and as code
            hh = StringIO.StringIO()
            GDprep.dump(hh, "%s_pic" % name, picdata)
            GDprep.dump(hh, "%s_chr" % name, chrdata)
            GDprep.dump(hh, "%s_pal" % name, paldata)
            t.code = hh.getvalue()
            open("../site/results/%s/%s.h" % (hash, name), "w").write(hh.getvalue())
            t.header = "/results/%s/%s.h" % (hash, name)
        return str(t)
    upload.exposed = True

import encode

def sanify(nm):
    def ok(c):
        if c.isalpha() or c.isdigit():
            return c
        else:
            return '_'
    return "".join([ok(c) for c in nm])

class Bg:
    def index(self):
        return encode.bgfront()
    index.exposed = True

    def upload(self, myFile, name, compress = False):
        compress = (compress != False)
        hash = "%08x" % random.getrandbits(32)
        dstdir = "../site/results/%s" % hash
        os.mkdir(dstdir)
        im = Image.open(myFile.file)
        name = sanify(name)
        im.save("/tmp/%08x.png" % random.getrandbits(32))
        encode.bgencode(dstdir, im, name, compress)
        raise cherrypy.HTTPRedirect("/results/%s" % hash, 301)
    upload.exposed = True

class Sp:
    def index(self):
        return encode.spfront()
    index.exposed = True

    def upload(self, myFile, name, palette, height, width, **kwargs):
        compress = 'compress' in kwargs
        hash = "%08x" % random.getrandbits(32)
        dstdir = "../site/results/%s" % hash
        os.mkdir(dstdir)
        im = Image.open(myFile.file)
        name = sanify(name)
        im.save("/tmp/%08x.png" % random.getrandbits(32))
        if im.mode in ["L", "P"]:
            im = im.convert("RGBA")
        encode.spencode(dstdir, im, name, compress, (int(width), int(height)), palette)
        raise cherrypy.HTTPRedirect("/results/%s" % hash, 301)
    upload.exposed = True

class Lossy:
    def index(self):
        return encode.lossyfront()
    index.exposed = True

    def upload(self, myFile, name, compress = False):
        compress = (compress != False)
        hash = "%08x" % random.getrandbits(32)
        dstdir = "../site/results/%s" % hash
        os.mkdir(dstdir)
        im = Image.open(myFile.file)
        name = sanify(name)
        im.save("/tmp/%08x.png" % random.getrandbits(32))
        encode.lossyencode(dstdir, im, name, 255)
        raise cherrypy.HTTPRedirect("/results/%s" % hash, 301)
    upload.exposed = True

class Test:
    def index(self):
        return str(ix())
    index.exposed = True
    bg = Bg()
    bg.exposed = True
    sp = Sp()
    sp.exposed = True
    lossy = Lossy()
    lossy.exposed = True
        
class Tools:
    def index(self):
        return str(ix())
    index.exposed = True
    bg = Bg()
    bg.exposed = True
    sp = Sp()
    sp.exposed = True
    lossy = Lossy()
    lossy.exposed = True
        
class Top:
    live = Live()
    live.exposed = True
    test = Test()
    test.exposed = True
    tools = Tools()
    tools.exposed = True
    def default(self, attr='abc'):
        raise cherrypy.HTTPRedirect("/prod/g" + attr[1:].upper(), 301)
    default.exposed = True
    
import os.path
# tutconf = os.path.join(os.path.dirname(__file__), 'tutorial.conf')

if __name__ == '__main__':
    # CherryPy always starts with app.root when trying to map request URIs
    # to objects, so we need to mount a request handler root. A request
    # to '/' will be mapped to HelloWorld().index().
    cherrypy.quickstart(Top())
else:
    # This branch is for the test suite; you can ignore it.
    cherrypy.tree.mount(WelcomePage(), config=tutconf)
