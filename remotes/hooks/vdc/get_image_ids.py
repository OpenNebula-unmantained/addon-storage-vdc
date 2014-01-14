#!/usr/bin/python

import MySQLdb
import xml.etree.ElementTree as ET
import os
import sys

hostname = os.uname()[1]

def xmlParse(elements,xml):
  """ parse an XML blob into a hierarchical map """
  for elem in xml:
    if elem.getchildren() == []:
      elements[elem.tag] = elem.text
      continue

    sub = {}
    xmlParse(sub,elem.getchildren())
    if elements.has_key(elem.tag):
      orig = elements[elem.tag]

      if type(orig) <> type([]): orig = [orig]
      sub=[sub]
      elements[elem.tag] = orig+sub
    else:
      elements[elem.tag] = sub

def getPath(vmid):
  """ get the original path of an image """
  cur.execute("SELECT * FROM image_pool WHERE oid = '%s'" % imid)
  rows = cur.fetchall()
  if len(rows) <> 1: return ""
  elements = {}
  xmlParse(elements,ET.fromstring(rows[0]['body']))
  return elements.get('PATH')


db = MySQLdb.connect(host="nebula",user="oneadmin",passwd="oneadmin",db="opennebula")
cur = db.cursor(MySQLdb.cursors.DictCursor)
#cur.execute("FLUSH QUERY CACHE");

output=""
vmid=int(sys.argv[1])
if len(sys.argv)>2:
  path=sys.argv[2].split("/")[-1]
else:
  path=""

cur.execute("SELECT * FROM vm_pool WHERE oid = '%s'" % vmid)
rows = cur.fetchall()
for row in rows:
  elements = {}
  xmlParse(elements,ET.fromstring(row['body']))
  temp = elements.get('TEMPLATE',None)
  if not temp: continue
  disk = temp.get('DISK',None)
  if not disk: continue
  if type(disk) <> type([]): disk = [disk]
  for d in disk:
    if d['TM_MAD']    <> 'vdc':    continue
    imid = d['IMAGE_ID']
    if getPath(imid) == "REPLICA":
        print "IS_REPLICA='YES'"

    source = d['SOURCE'].split("/")[-1]
    if len(path) and (source <> path): continue

    print 'NAME="ON_%s_%s"' % (str(imid),str(vmid))
    print 'STORE="ONE_%s"' % str(imid)
    print 'CACHE="ONE_%s"' % str(vmid)
    sys.exit(0)

print 'NAME=""'
print 'STORE=""'
print 'CACHE=""'
sys.exit(1)

