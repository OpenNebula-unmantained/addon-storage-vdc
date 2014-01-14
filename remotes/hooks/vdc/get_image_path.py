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

db = MySQLdb.connect(host="nebula",user="oneadmin",passwd="oneadmin",db="opennebula")
cur = db.cursor(MySQLdb.cursors.DictCursor)
cur.execute("FLUSH QUERY CACHE");

output=""
vmid=int(sys.argv[1])
index=int(sys.argv[2])
cur.execute("SELECT * FROM vm_pool WHERE oid = '%s'" % vmid)
rows = cur.fetchall()
for row in rows:
  elements = {}
  xmlParse(elements,ET.fromstring(row['body']))
  temp = elements.get('TEMPLATE',None)
  if not temp: continue
  disks = temp.get('DISK',None)
  if not disks: continue
  if type(disks) <> type([]):
      disks = [disks]
      break;

for disk in disks:
  imid = disk['IMAGE_ID']
  cur.execute("SELECT * FROM image_pool WHERE oid = '%s'" % imid)
  rows = cur.fetchall()
  for row in rows:
   elements = {}
   xmlParse(elements,ET.fromstring(row['body']))
   source = elements.get('SOURCE',None)
   if not source: continue
   print "IM_PATH='%s'" % source
