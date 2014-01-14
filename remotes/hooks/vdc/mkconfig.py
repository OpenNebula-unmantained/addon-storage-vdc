#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb
import xml.etree.ElementTree as ET
import os
import sys
import time
import fcntl
from syslog import syslog,LOG_INFO
from time import sleep

CONFIG_FILE = "/etc/vdc/config.new"
CONFIG_LIVE = "/etc/vdc/config"
CONFIG_LOCK = "/etc/vdc/config.lock"
VDC_NAMES = []
hostname = os.uname()[1]

def LockFile(file):
  """ add an advisory lock to a file """
  try:
    fcntl.flock(file.fileno(),fcntl.LOCK_EX)
    return True
  except:
    syslog(LOG_INFO,"* mkconfig :: ERROR locking config file")
    return False

def UnlockFile(file):
  """ remove an advisory lock from a file """
  fcntl.flock(file.fileno(),fcntl.LOCK_UN)

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
cursor = db.cursor(MySQLdb.cursors.DictCursor)
cursor.execute("FLUSH QUERY CACHE");

syslog(LOG_INFO,"* mkconfig :: ++++")
syslog(LOG_INFO,"* mkconfig :: Acquiring configuration file")
while True:

  lck = open(CONFIG_LOCK,"w")
  if not lck:
    syslog(LOG_INFO,"* mkconfig :: config file [%s] is missing" % CONFIG_LOCK)
    sys.exit(1)

  syslog(LOG_INFO,"* mkconfig :: Acquiring configuration lock")
  if LockFile(lck): break
  lck.close()
  time.sleep(1)

syslog(LOG_INFO,"* mkconfig :: Opening new target")
dst = open(CONFIG_FILE,"w")
if not dst:
  syslog(LOG_INFO,"* mkconfig :: config file [%s] is missing" % CONFIG_FILE)
  sys.exit(1)

dst.truncate()
dst.write("#\n# VDC Config file\n")
dst.write("# AUTO-GENERATED - DO NOT EDIT!\n#\n")
dst.write("[global]\n  host = "+hostname+"\n")
dst.write("  proto = lsfs\n")

cursor.execute("SELECT * FROM image_pool")
for row in cursor.fetchall():
    xml = {}
    xmlParse(xml,ET.fromstring(row['body']))
    dsid = row['oid']
    desc = xml.get('NAME','Unknown')
    path = xml.get('SOURCE',None)
    host = xml.get('DATASTORE',None)
    temp = xml.get('TEMPLATE',None)
    size = temp.get('CAPACITY',None)

    if host <> hostname: continue
    if size == None:
        dst.write('# Error : no size for %s' % "ONE_"+str(dsid))
        continue

    name = "ONE_"+str(dsid)
    dst.write("[%s]\n" % name)
#    dst.write("  desc = %s\n" % desc)
    dst.write("  path = %s\n" % path)
    dst.write("  size = %s\n" % size)

dst.write('#\n# Non-persistent images here ...\n#\n')

cursor.execute("SELECT * FROM vdc_pool")
for row in cursor.fetchall():
    #print row
    #print row['host'],hostname
    if row['host'] <> hostname: continue

    store = row['store']
    #if row['size'] == None:
   #     dst.write('# Error : no size for %s' % store)
   #     continue

    #print store
    dst.write("[%s]\n" % store)
    dst.write("  path = %s\n" % row['path'])
    dst.write("  size = %s\n" % row['size'])


dst.close()
syslog(LOG_INFO,"* mkconfig :: Target generation complete")

while True:

  syslog(LOG_INFO,"* mkconfig :: Acquiring live configuration file")
  dst = open(CONFIG_LIVE,"r")
  if not dst:
    syslog(LOG_INFO,"* mkconfig :: config file [%s] is missing" % CONFIG_FILE)
    sys.exit(1)

  syslog(LOG_INFO,"* mkconfig :: Acquiring live lock [contend with server]")
  if LockFile(dst): break
  dst.close()
  time.sleep(1)

try:
  syslog(LOG_INFO,"* mkconfig :: Renaming (new->live)")
  os.rename(CONFIG_FILE,CONFIG_LIVE)
  syslog(LOG_INFO,"* mkconfig :: Success ...")
except IOError as e:
  syslog(LOG_INFO,"* CRITICAL :: Error installing new config [err=%d]" % e.errno)

syslog(LOG_INFO,"* mkconfig :: Releasing live lock")
UnlockFile(dst)
dst.close()
syslog(LOG_INFO,"* mkconfig :: Releasing config lock")
UnlockFile(lck)
lck.close()
syslog(LOG_INFO,"* mkconfig :: ++++")
sys.exit(0)



#cur.execute("SELECT * FROM image_pool")
#for row in cur.fetchall():
#  elements = {}
#  xmlParse(elements,ET.fromstring(row['body']))
#  if int(elements['DATASTORE_ID']) <> oid: continue
# persist = int(elements['PERSISTENT'])

#  id   = elements.get('ID','0')
#  path = elements.get('SOURCE','none')
#  temp = elements.get('TEMPLATE',{})
#  size = temp.get('CAPACITY','10G')
#  used = elements.get('VMS',None)
#  if(not used): continue

#  for vmid in images.get(id,[]):
#    name = "ONE_"+str(id)+"_"+str(vmid)
#    dst.write("[%s]\n" % name)
#    dst.write("  size = %s\n" % size)
#    dst.write("  proto = lsfs\n")
#    if not persist:
#      cur.execute("SELECT * FROM vdc WHERE name = '"+name+"'")
#      rows = cur.fetchall()
#      if not len(rows):
#        # sleep(2)
##       cur.execute("SELECT * FROM vdc WHERE name = '"+name+"'")
#        rows = cur.fetchall()
#        # FIXME :: THIS is a timing issue, needs a better fix
#        if not len(rows): continue
#      row = rows[0]
#      path = row['path']
#    dst.write("  path = %s\n" % path)

#images={}
#cur.execute("SELECT * FROM vm_pool WHERE state <> 6")
#rows = cur.fetchall()
#for row in rows:
#  elements = {}
#  xmlParse(elements,ET.fromstring(row['body']))
#  temp = elements.get('TEMPLATE',None)
#  if not temp: continue
#  disk = temp.get('DISK',None)
#  if not disk: continue
#  if type(disk) <> type([]): disk = [disk]
#  syslog(LOG_INFO,str(disk))
#  for d in disk:
#    if d['TM_MAD']    <> 'vdc':    continue
#    if d['DATASTORE'] <> hostname: continue
#    vmid = row['oid']
#    imid = d['IMAGE_ID']
#    if not images.has_key(imid):
#      images[imid]=[vmid]
#    else:
#      images[imid]=images[imid]+[vmid]

#syslog(LOG_INFO,str(images))

#cur.execute("SELECT * FROM datastore_pool WHERE name = '%s'" % hostname)
#rows = cur.fetchall()
#if( len(rows) <> 1 ):
#  print("# ERROR :: needs to be exactly one datastore with name '%s', found %s",hostname,len(rows))
#  sys.exit(1)
#oid = int(rows[0]['oid'])
