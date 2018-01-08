#!/usr/bin/env python
"""
  Script for parsing input file.
"""
import os
import unicodedata


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
 
    try:
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False

def parser(input_file, password):
    inp = {'pw':         password,
           'work_dir':   os.getcwd(),
           'output_dir': os.getcwd() + '/output/'}

    with open(input_file, 'r') as fid:
        while True:
            line = fid.readline()
            if not line:
              break

            line = line.split()
            if len(line) < 2 or '#' in line[0]:
                continue 
            
            key, val = line[:2]
            if is_number(val):
                val = float(val)
                if (val).is_integer():
                    inp[key] = int(val)  # int
                else:
                    inp[key] = val       # float
            else:
                inp[key] = val           # string
    return inp


if __name__ == '__main__':
    pass
