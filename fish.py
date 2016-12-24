# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import re
import sys

class Fish:
    def __init__(self):
        self.ns = {'ksj': 'http://nlftp.mlit.go.jp/ksj/schemas/ksj-app',
                   'gml': 'http://www.opengis.net/gml/3.2',
                   'xlink': 'http://www.w3.org/1999/xlink',
                   'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

        self.id = -200000000000

        self.osm = ET._Element('osm')
        self.osm.set("version", "0.6")


    def parse(self, file):
        self.root = ET.parse(file)

    def load(self, string):
        self.root = ET.fromstring(string)

    def findLoc(self, id):
        """

        :rtype: ET.Element
        """
        ns = {'ksj': 'http://nlftp.mlit.go.jp/ksj/schemas/ksj-app',
                  'gml': 'http://www.opengis.net/gml/3.2',
                   'xlink': 'http://www.w3.org/1999/xlink',
                   'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

        key = './/*[@gml:id="'+ id + '"]'
        loc = self.root.find(key, ns)

        return loc


    def locToOSM(self, loc):
        poslist = loc.find(".//gml:posList", self.ns)
        loctext = poslist.text

        way = ET.SubElement(self.osm, 'way')
        way.set('version', '1')
        way.set('timestamp', '2015-12-01T21:37:45Z')

        initX = None
        initY = None
        initId = None
        lastId = None
        for line in loctext.split('\n'):

            if line == '':
                continue
            xy = line.split()

            if len(xy) == 0:
                continue

            self.id -= 1

            [x, y] = xy
            if initX == None:
                initX = x;
            if initY == None:
                initY = y
            if initId == None:
                initId = self.id

            nd = ET.SubElement(way, 'nd')

            #close polygon
            if initX == x and initY == y and initId != self.id:
                nd.set('ref', str(initId))
                lastId = initId
            else:
                node = ET.SubElement(self.osm, 'node')
                node.set('lat', str(x))
                node.set('lon', str(y))
                node.set('id', str(self.id))
                node.set('version', '1')
                node.set('timestamp', '2015-12-01T21:37:45Z')

                nd.set('ref', str(self.id))
                lastId = self.id

        if(lastId != initId):
            nd = ET.SubElement(way, 'nd')
            nd.set('ref', str(initId))

        self.tag(way, 'note', "National-Land Numerical Information")
        self.tag(way, 'note:ja', "National-Land Numerical Information")

        self.id -= 1
        print self.id
        way.set('id', str(self.id))

        locid = loc.get("{http://www.opengis.net/gml/3.2}id")
        self.tag(way, "KJS2:gml:id", locid)

        return way


    def tag(self, e, key, value):
        if value != None:
            tag = ET.SubElement(e, 'tag')
            tag.set('k', key)
            tag.set('v', value)


    def fisharea(self):
        fishrights = self.root.findall('ksj:FisheryRightSetLine', self.ns)
        ksj_type = '{http://nlftp.mlit.go.jp/ksj/schemas/ksj-app}type'
        ksj_right_holder = '{http://nlftp.mlit.go.jp/ksj/schemas/ksj-app}rightHolderName'
        ksj_product = '{http://nlftp.mlit.go.jp/ksj/schemas/ksj-app}fisheryProduct'

        for f in fishrights:

            id = self.fishrightId(f)

            type = f.find(ksj_type)
            if type != None:
                type_t = type.text

            if type_t in {'11', '12', '13', '30'}:
                loc = self.findLoc(id)
                way = self.locToOSM(loc)
                self.tag(way, 'KSJ2:fish_right:type', type.text)
                self.tag(way, 'seamark:type', 'marine_farm')

                holder = f.find(ksj_right_holder)
                if holder != None:
                    self.tag(way, 'KSJ2:fish_right:holder', holder.text)

                product = f.find(ksj_product)
                if product != None:
                    self.tag(way, 'name', product.text)
                    self.setSeamarkCategory(way, product.text)

            else:
                pass


    def setSeamarkCategory(self, way, product):
        if product == None:
            return

        if re.compile(u'シンジュ').search(product):
            self.tag(way, 'seamark:marine_farm:category', 'pearl_culture')
        elif re.compile(u'エビ|ウニ').search(product):
            self.tag(way, 'seamark:marine_farm:category', 'crustaceans')
        elif re.compile(u'ギヨルイ|ブリ|ハマチ|カンパチ|ヒラマサ|タイ|アジ|ヒラメ|フグエビ|メジナ|メバル|チヌ|ソノタギヨルイアミシキリ|コワリシキ|サケ|ザケ').search(product):
            self.tag(way, 'seamark:marine_farm:category', 'fish')
        elif re.compile(u'ワカメ|コンブ|ノリ|モズク|アオサ|ヒビ').search(product):
            self.tag(way, 'seamark:marine_farm:category', 'seaweed')
        elif re.compile(u'カイ|ガイ|カキ|ハマグリ|アサリ|シジミ').search(product):
            self.tag(way, 'seamark:marine_farm:category', 'oysters_mussels')


    def fishrightId(self, fr):
        xlink = '{http://www.w3.org/1999/xlink}href'
        location = fr.find('ksj:location', self.ns)
        id = location.get(xlink)
        return id.replace('#', '')


if __name__ == '__main__':
    input = sys.stdin
    output = sys.stdout

    argv = sys.argv
    argc = len(sys.argv)

    if(argc == 3):
        input = argv[1]
        output = argv[2]
    else:
        print "python fish.py <inputfile> <outputfile>"

    fish = Fish()

    fish.parse(input)

    fish.fisharea()
    et = ET.ElementTree(fish.osm)
    et.write(output, encoding='utf-8', xml_declaration=True)


