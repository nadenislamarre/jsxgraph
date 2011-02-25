#!/usr/bin/env python
# -*- coding: utf-8 -*-


license = """/*
    Copyright 2008-2011
        Matthias Ehmann,
        Michael Gerhaeuser,
        Carsten Miller,
        Bianca Valentin,
        Alfred Wassermann,
        Peter Wilfahrt

    This file is part of JSXGraph.

    JSXGraph is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    JSXGraph is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with JSXGraph.  If not, see <http://www.gnu.org/licenses/>.
*/
    """

    
import sys;
# Parse command line options
import getopt;

# Used for makeRelease & makeCompressor
import os
import re
import tempfile
import shutil


# Default values for options. May be overridden via command line options
yui = "~/public_html/jsxgraph/trunk/tools/yuicompressor-2.4.2"
jsdoc = "~/public_html/jsxgraph/jsdoc_toolkit-2.3.2/jsdoc-toolkit"
output = "distrib"
version = None


'''
    Prints some instructions on how to use this script
'''
def usage():
    print
    print "Usage:  python", sys.argv[0], "[OPTIONS]... TARGET"
    print "Compile and minify the JSXGraph source code."
    print
    print "Options:"
    print "  -h, --help             Display this help and exit."
    print "  -j, --jsdoc=PATH       Search for jsdoc-toolkit in PATH."
    print "  -o, --output=PATH      Override the default output path distrib/ by PATH."
    print "  -v, --version=VERSION  Use VERSION as release version for proper zip archive and"
    print "                         folder names."
    print "  -y, --yui=PATH         Search for YUI Compressor in PATH."
    print
    print "Targets:"
    print "  Core                   Concatenates and minifies JSXGraph source files into"
    print "                         distrib/jsxgraphcore.js ."
    print "  Release                Makes Core and Docs and creates distribution ready zip archives"
    print "                         in distrib/ ."
    print "  Docs                   Generate documentation from source code comments. Uses"
    print "                         jsdoc-toolkit."
    print "  Compressor             Minify and create a zip archive for JSXCompressor."
    print "  All                    Makes JSXGraph and Compressor."
    

'''
    Search for line
    baseFile = 'AbstractRenderer,...,gunzip';
    and return list of filenames
'''
def findFilenames(filename):
    lines = open(filename).readlines()
    expr = re.compile("baseFiles\s*=\s*('|\")([\w,\s]+)('|\")")
    for el in lines:
        el = re.compile("\s+").sub("",el) # Replace whitespace
        r = expr.search(el)
        if r and r.groups()[1]!='gxt':
            files = r.groups()[1].split(',')
            return files  # return all files in loadjsxgraph.js
    return []

'''
    Generate jsxgraphcore.js and place it in <output>
'''
def makeCore():
    global yui, jsdoc, version, output, license

    print "Making Core..."
    
    jstxt = ''
    license = ("/* Version %s */\n" % version) + license

    # Take the source files and write them into jstxt
    loader = ['loadjsxgraphInOneFile']
    for f in loader:
        print 'take ', f
        jstxt += open('src/'+f+'.js','r').read()
        jstxt += '\n';

    files = findFilenames('src/loadjsxgraph.js')
    for f in files:
        print 'take ', f
        jstxt += open('src/'+f+'.js','r').read()
        jstxt += '\n';
    renderer = ['SVGRenderer','VMLRenderer','CanvasRenderer']
    for f in renderer:
        print 'take ', f
        jstxt += open('src/'+f+'.js','r').read()
        jstxt += '\n';

    tmpfilename = tempfile.mktemp()
    fout = open(tmpfilename,'w')
    fout.write(jstxt)
    fout.close()

    # Prepend license text
    coreFilename = output + "/jsxgraphcore.js"
    fout = open(coreFilename,'w')
    fout.write(license)
    fout.close()

    # Minify; YUI compressor from Yahoo
    s = "java -jar " + yui + "/build/yuicompressor*.jar --type js " + tmpfilename + " >>" + coreFilename
    print s
    os.system(s)
    os.remove(tmpfilename)

'''
    Generate JSXGraph HTML reference, zip it and place the archive in <output>
'''
def makeDocs(afterCore = False):
    global yui, jsdoc, version, output
    
    jsd = os.path.expanduser(jsdoc)
    if afterCore:
        out = output
    else:
        out = "distrib"

    print "Making Docs"

    print "Updating jsdoc-template and plugin"

    try:
        # cp ../doc/jsdoc-tk/plugins/* $ROOT/app/plugins/
        shutil.copy("doc/jsdoc-tk/plugins/jsxPseudoClass.js", jsd + "/app/plugins/jsxPseudoClass.js")

        # cp -r ../doc/jsdoc-tk/template/* $ROOT/templates/jsdoc
        shutil.rmtree(jsd + "/templates/jsx/", True)
        shutil.copytree("doc/jsdoc-tk/template", jsd + "/templates/jsx")

        # mkdir $ROOT/templates/jsdoc/static
        # cp ../distrib/jquery.min.js $ROOT/templates/jsdoc/static
        # cp ../distrib/jsxgraphcore.js $ROOT/templates/jsdoc/static
        # cp ../distrib/jsxgraph.css $ROOT/templates/jsdoc/static
        shutil.copy("distrib/jquery.min.js", jsd + "/templates/jsx/static")
        shutil.copy(out + "/jsxgraphcore.js", jsd + "/templates/jsx/static")
        shutil.copy("distrib/jsxgraph.css", jsd + "/templates/jsx/static")
    except IOError as (errno, strerror):
        print "Error: Can't update jsdoc-toolkit template and/or plugin:",strerror
        sys.exit(2)

    #FILELIST=$(cat ../src/loadjsxgraph.js | grep "baseFiles\s*=\s*'\(\w*,\)\+" | awk -F \' '{ print $2 }' | sed 's/,/.js ..\/src\//g')
    files = findFilenames('src/loadjsxgraph.js')
    filesStr = "src/loadjsxgraph.js src/" + ".js src/".join(files) + ".js src/SVGRenderer.js src/VMLRenderer.js src/CanvasRenderer.js"
    
    #java -jar $ROOT/jsrun.jar $ROOT/app/run.js -a -v -t=$ROOT/templates/jsdoc -d=docs ../src/loadjsxgraph.js ../src/$FILELIST.js ../src/SVGRenderer.js ../src/VMLRenderer.js
    os.system("java -jar " + jsd + "/jsrun.jar " + jsd + "/app/run.js -a -v -t=" + jsd + "/templates/jsx -d=tmp/docs " + filesStr)
    
    #zip -r tmp/docs.zip tmp/docs/
    os.system("cd tmp && zip -r docs-" + version + ".zip docs/ && cd ..")
    shutil.move("tmp/docs-" + version + ".zip", output + "/docs-" + version + ".zip")
    

'''
    Make targets Core and Docs and create distribution-ready zip archives in <output>
'''
def makeRelease():
    print "Make Release"
    
    makeCore()
    makeDocs(True)
    
    shutil.copy(output + "/jsxgraphcore.js", "tmp/jsxgraphcore.js")
    shutil.copy("README", "tmp/README")
    shutil.copy("LICENSE", "tmp/LICENSE")
    shutil.copy("distrib/jsxgraph.css", "tmp/jsxgraph.css")
    os.system("cd tmp && zip -r jsxgraph-" + version + ".zip docs/ jsxgraphcore.js jsxgraph.css README LICENSE && cd ..")
    shutil.move("tmp/jsxgraph-" + version + ".zip", output + "/jsxgraph-" + version + ".zip")


'''
    Make JSXCompressor, a JSXGraph subproject
'''
def makeCompressor(afterCore = False):
    global yui, jsdoc, version, output, license

    print "Make JSXCompressor"

    if afterCore:
        out = output
    else:
        out = "distrib"

    jstxt = 'JXG = {};\n'
    jstxt += 'JXG.decompress = function(str) {return unescape((new JXG.Util.Unzip(JXG.Util.Base64.decodeAsArray(str))).unzip()[0][0]);};\n'

    # Take the source files and write them into jstxt
    loader = ['Util']
    for f in loader:
        print 'take ', f
        jstxt += open('src/'+f+'.js','r').read()
        jstxt += '\n';


    tmpfilename = tempfile.mktemp()
    fout = open(tmpfilename,'w')
    fout.write(jstxt)
    fout.close()

    # Prepend license text
    coreFilename = output + "/jsxcompressor.js"
    fout = open(coreFilename, 'w')
    fout.write(license)
    fout.close()

    # Minify 
    # YUI compressor from Yahoo
    s = 'java -jar ' + yui + '/build/yuicompressor*.jar --type js ' + tmpfilename + ' >>' + coreFilename
    print s
    os.system(s)
     
    os.remove(tmpfilename)
    os.system("cp %s %s" % (coreFilename, 'JSXCompressor/'))
    # If makeCore has been called just befure, make sure you grab the newest version
    os.system("cp %s %s" % (out + '/jsxgraphcore.js', 'JSXCompressor/'))
    os.system("cp %s %s" % ('distrib/prototype.js', 'JSXCompressor/'))
    os.system("cp %s %s" % ('distrib/jsxgraph.css', 'JSXCompressor/'))
    os.system("rm JSXCompressor/*~")
    os.system("zip -r " + output + "/jsxcompressor.zip JSXCompressor/*")


'''
    Make targets Release and Compressor
'''
def makeAll():
    makeRelease()
    makeCompressor(True)
    

def main(argv):
    global yui, jsdoc, version, output

    try:
        opts, args = getopt.getopt(argv, "hy:j:v:o:", ["help", "yui=", "jsdoc=", "version=", "output="])
    except getopt.GetoptError as (errono, strerror):
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(2)
        elif opt in ("-j", "--jsdoc"):
            jsdoc = arg
        elif opt in ("-o", "--output"):
            output = os.path.expanduser(arg)
        elif opt in ("-v", "--version"):
            version = arg
        elif opt in ("-y", "--yui"):
            yui = arg

    target = "".join(args)

    # Search for the version and print it before the license text.
    if not version:
        expr = re.compile("JSXGraph v(.*) Copyright")
        r = expr.search(open("src/jsxgraph.js").read())
        version = r.group(1)

    try:
        # Create tmp directory and output directory
        if not os.path.exists(output):
            os.mkdir(output)
        if not os.path.exists("tmp"):
            os.mkdir("tmp")

        # Call the target make function
        globals()["make" + target]()
        shutil.rmtree("tmp/")
    except KeyError:
        # Oooops, target doesn't exist.
        print "Error: Target", target, "does not exist."
        usage()
        shutil.rmtree("tmp/")
        sys.exit(1)
    except IOError:
        print "Error: Can't create tmp directories."
        sys.exit(1)

if __name__ == "__main__":
    main(sys.argv[1:])