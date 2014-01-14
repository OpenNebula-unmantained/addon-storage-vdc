#!/usr/bin/python

import MySQLdb
import xml.etree.ElementTree as ET
import os
from syslog import syslog,LOG_INFO
from time import sleep
from sys import argv,exit

hostname = os.uname()[1]

def xmlParse(elements,xml):
  """ parse an XML blob into a hierarchical map """
  for elem in xml:
    if elem.getchildren() <> []:
      elements[elem.tag] = {}
      xmlParse(elements[elem.tag],elem.getchildren())
    else:
      elements[elem.tag] = elem.text

db = MySQLdb.connect(host="127.0.0.1",user="root",passwd="",db="opennebula")
cur = db.cursor(MySQLdb.cursors.DictCursor) 

def Get(table,key,val,keys,debug):
  """ interrogate the XML """
  try:
    cur.execute("SELECT * FROM %s where %s = '%s'" % (table,key,val))
    rows = cur.fetchall()
    if(len(rows)==0): return "none"
    elements = {}
    xmlParse(elements,ET.fromstring(rows[0]['body']))

    if debug: print elements

    keys = keys.split(",")
    for k in keys:
      if elements.has_key(k):
        elements = elements[k]
      else:
        return "none"
    return elements

  except:
    pass
  return "none"

def do_getlvm(host):
    """ return the logical volume the cache is sitting on """
    print "CACHE_LVM='%s'"   % Get("host_pool","name",host,"TEMPLATE,VDC_CACHE_LVM",False)

def do_env(vmid,dsid,host,path):
    """ set environment variable from SQL """

    if len(path):
        path=path.split("/")
        if len(path): path = path[-1]

    replica_ds = "none"
    replica_store = "none"
    replica_id = "none"
    is_replica = "NO"
    store = "none"
    cache = "none"
    persistent = "1"
    capacity = "none"

    cache_size  = Get("vm_pool","oid",str(vmid),"TEMPLATE,CONTEXT,VDC_CACHE_SIZE",False)
    cache_lvm   = Get("host_pool","name",host,"TEMPLATE,VDC_CACHE_LVM",False)
    ds_name     = Get("datastore_pool","oid",str(dsid),"NAME",False)
    replica_id  = Get("vm_pool","oid",str(vmid),"USER_TEMPLATE,REPLICA",False)

    disks  = Get("vm_pool","oid",str(vmid),"TEMPLATE,DISK",False)
    if type(disks) <> type([]): disks = [disks]
    for disk in disks:
        if disk['TM_MAD'] <> 'vdc': continue
        imid = disk['IMAGE_ID']
        ipath = Get("image_pool","oid",str(imid),"PATH",False)
        persistent = Get("image_pool","oid",str(imid),"PERSISTENT",False)
        if ipath == "REPLICA": is_replica = "YES"
        source = disk['SOURCE'].split("/")[-1]
        if len(path) and (path <> source): continue

        if persistent=="1":
            store = "ONE_%s" % str(imid)
        else:
            store = "ONE_%s_%s" % (str(imid),str(vmid))

        cache = "ONE_%s" % str(vmid)
        capacity = Get("image_pool","oid",str(imid),"TEMPLATE,CAPACITY",False)

        if not len(path): break

    if replica_id <> "none":
        replica_ds = Get("image_pool","oid",str(replica_id),"DATASTORE",False)
        replica_store = "ONE_%s" % replica_id

    print "DS_NAME='%s'" % ds_name
    print "CACHE_SIZE='%s'" % cache_size
    print "CACHE_LVM='%s'" % cache_lvm
    print "REPLICA_DS='%s'" % replica_ds
    print "REPLICA_STORE='%s'" % replica_store
    print "REPLICA_ID='%s'" % replica_id
    print "IS_REPLICA='%s'" % is_replica
    print "STORE='%s'" % store
    print "CACHE='%s'" % cache
    print "PERSISTENT='%s'" % persistent
    print "CAPACITY='%s'" % capacity
    return

def do_ln(vmid,dsid,host):
  """ print an environment string for the ln command """
  print "DS_NAME='%s'"     % Get("datastore_pool","oid",str(dsid),"NAME",False)
  print "CACHE_SIZE='%s'"  % Get("vm_pool","oid",str(vmid),"TEMPLATE,CONTEXT,VDC_CACHE_SIZE",False)
  print "CACHE_LVM='%s'"   % Get("host_pool","name",host,"TEMPLATE,VDC_CACHE_LVM",False)

  replica = Get("vm_pool","oid",str(vmid),"USER_TEMPLATE,REPLICA",False)
  if replica <> "none":
    ds = Get("image_pool","oid",replica,"DATASTORE",False)
    print "REPLICA_DS='%s'" % ds
    print "REPLICA_STORE='ONE_%s'" % replica

  print "REPLICA_ID='%s'"  % replica
  return

def do_add(store,path,host,capacity):
  """ add an entry to the temporary db """  
  cur.execute("INSERT INTO vdc_pool (store,path,host,size) VALUES ('%s','%s','%s','%s')" % (store,path,host,capacity))
  return

def do_getpath(name):
  """ look up the path of a non persistent VM """
  cur.execute("SELECT path FROM vdc_pool WHERE name = '%s'" % name)
  rows = cur.fetchall()
  if(not len(rows)):
    print "IM_PATH=''"
    return

  print "IM_PATH='%s'" % rows[0]['path']
  return

def do_del(store):
    """ check if we need to delete a transient copy """
    cur.execute("SELECT * FROM vdc_pool WHERE store = '"+store+"'")
    rows = cur.fetchall()
    path = ''
    if len(rows):
        path= rows[0]['path']
        cur.execute("DELETE FROM vdc_pool WHERE store = '"+store+"'")

    print "IM_PATH='%s'" % path
    return

#print "# 4"

if(len(argv)<2):
  print "Usage: ln <vmid> <dsid>"
  exit(1)

if argv[1] == "ln":
  if len(argv) < 5:
    print "Usage: "+argv[0]+" ln <vmid> <dsid> <host>"
    exit(1)
  do_ln(argv[2],argv[3],argv[4])
  exit(0)

elif argv[1] == "env":
    #print "# 5"
    if len(argv) < 6:
      print "Usage: "+argv[0]+" ln <vmid> <dsid> <host> <path>"
      exit(1)
    #print "# 6"
    do_env(argv[2],argv[3],argv[4],argv[5])
    #print "# 7"
    exit(0)

elif argv[1] == "add":
  if len(argv)<6:
    print "Usage: "+argv[0]+" add <store> <path> <host> <size>"
    exit(1)
  do_add(argv[2],argv[3],argv[4],argv[5])

elif argv[1] == "del":
  if len(argv)<3:
    print "Usage: "+argv[0]+" del <store>"
    exit(1)
  do_del(argv[2])

elif argv[1] == "getpath":
  if len(argv)<3:
    print "Usage: "+argv[0]+" del <name>"
    exit(1)
  do_getpath(argv[2])

elif argv[1] == "getlvm":
  if len(argv)<3:
    print "Usage: "+argv[0]+" getlvm <host>"
    exit(1)
  do_getlvm(argv[2])

else:
  print "Unknown command: "+argv[0]
  exit(1)

exit(0)
