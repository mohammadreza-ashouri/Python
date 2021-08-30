#!/usr/bin/python3
'''
Join hdf5 files into one and **remove** individual files

Usage:
  hdf5join.py joined.hdf5 Test*.hdf5
'''
import sys, h5py, os

h5joined = h5py.File(sys.argv[1],'w')
print('Create file:',sys.argv[1])
for h5Name in sys.argv[2:]:
  print('  Merge and delete:',h5Name)
  h5 = h5py.File(h5Name,'r')
  h5.copy('/', h5joined, h5Name)
  h5.close()
  os.remove(h5Name)
h5joined.close()