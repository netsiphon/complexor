#!/usr/bin/env python


# complexor


import os
import sys
import argparse
from operator import xor


DEBUG = True
charSet = {}
charSetCheck = {}
file_size = 0
max_key_size = 1024


class FileTypes:
    def __init__(self):
        self.types = []
        self.typeLookup = {}


class FileType:
    def __init__(self):
        self.id = None
        self.fileMagic = []
        self.name = ""


"""
    Main -
    in_file, out_file, key, offset, write_offset
"""


def main(args):
    try:
        pos = 0
        keyHint = ''
        begin_offset = 0
        offset_chars = ''
        detection_offset = -1
        key = ''
        # Input file
        try:
            in_file = open(args.in_file, 'rb')
        except:
            print 'Fatal Error: Could not open input file!'
            sys.exit(0)
        # Output file
        try:
            out_file = open(args.out_file, 'wb')
        except:
            print 'Fatal Error: Could not open output file!'
            sys.exit(0)
        # Need file size to make sure we can't offset too far
        file_size = os.path.getsize(args.in_file)
        if args.k:
            key = args.k
            len_key = len(key)
            if len_key > max_key_size:
                key[0:max_key_size - 1]
                len_key = len(key)
                print('BAD KEY: Key Too Large. Reducing size to maximum of ' +
                      max_key_size + '.')
            if len_key < 1:
                print 'BAD KEY: Zero-sized Key. Please provide a valid key!'
                sys.exit(0)
            else:
                if file_size % len_key != 0:
                    print('BAD KEY: Key size doesn\'t match length of file.'
                          'Please provide a valid key!')
                    sys.exit(0)
        if args.b:
            begin_offset = args.b
            if begin_offset > file_size:
                begin_offset = file_size
            # Read offset bytes
            if begin_offset > 0:
                offset_chars = in_file.read(begin_offset)
                if args.w is True:
                    out_file.write(offset_chars)
                    pos = pos + begin_offset
                    offset_chars = ''
        if args.x and not args.k:
            detection_offset = args.x
            if detection_offset > file_size:
                detection_offset = file_size
            # Attempt to determine key
            if detection_offset >= 0:
                # Check against known characters for executable
                keyHint = checkHead(in_file.read(2))
                if DEBUG is True:
                    print 'KeyHint:"' + ''.join(keyHint) + '"'
                in_file.seek(file_size - detection_offset)
                charSet = findKeys(in_file, keyHint, detection_offset)
                key = findRepeatKey(charSet, keyHint, detection_offset)
                if DEBUG is True:
                    print 'RepeatedKey: ' + unicode(key)
                key = findLongKey(charSet, keyHint, detection_offset)
                if DEBUG is True:
                    print 'LongestKey: ' + unicode(key)
                if key != '':
                    key = ''.join(keyHint) + key
                    print 'DETECT KEY: Found Key \'' + key + '\''
                else:
                    print('DETECT KEY: Failed to detect key! '
                          'Try a larger detection offset.')
        if key != '':
            # Key as array of characters
            bKey = list(key)
            key_len = len(key)
            in_file.seek(begin_offset)
            byte = ''
            byte = in_file.read(1)
            pos = 0
            while byte != '':
                key_cur = bKey[pos % key_len]
                # Compare
                xor_out = chr(xor(ord(byte), ord(key_cur)))
                out_file.write(xor_out)
                # print 'Byte=' + byte + ';Key=' + key_cur + ';XOR:' + xor_out
                byte = in_file.read(1)
                pos += 1
            print('Done! ' + str(pos) + ' bytes written to ' +
                  args.out_file + '.')
        in_file.close
        out_file.close
    except Exception as e:
        print('Error:' + str(type(e)) + ':' + str(e) +
              ' at line: {}'.format(sys.exc_info()[-1].tb_lineno))
        in_file.close
        out_file.close
        sys.exit(0)


def checkHead(first_chars):
    exeHead = ['M', 'Z']
    keyStart = ['', '']
    if DEBUG is True:
        print 'FirstChars:' + first_chars
    if len(first_chars) == 2:
        keyStart[0] = chr(xor(ord(exeHead[0]), ord(first_chars[0])))
        keyStart[1] = chr(xor(ord(exeHead[1]), ord(first_chars[1])))
    return keyStart


def findKeys(in_file, keyStart, offset):
    try:
        file_size = os.path.getsize(args.in_file)
        keyChar = in_file.read(1)
        keyBuffer = ''
        keyBuffer = keyBuffer + keyChar
        if int(file_size/offset) % 2 == 0:
            mod_factor = 2
        else:
            mod_factor = 1
        in_file.seek(file_size - offset)
        while keyChar != '':
            keyLen = len(keyBuffer)
            if keyLen >= 2:
                if(keyBuffer[keyLen - 2:] == ''.join(keyStart) and keyLen %
                   mod_factor == 0):
                    # and file_size - (keyLen * int(offset/keyLen)) > 0:
                    keyBuffer = ''
            if keyChar in charSet:
                charSet[keyChar] += 1
            else:
                charSet[keyChar] = 1
            if keyBuffer in charSet:
                charSet[keyBuffer] += 1
            else:
                charSet[keyBuffer] = 1
            keyChar = in_file.read(1)
            keyBuffer = keyBuffer + keyChar
        debugCharSet(charSet)
        keys = charSet.keys()
        values = charSet.values()
        kLen = len(keys) - 1
        for k in range(kLen, -1, -1):
            key_length = len(keys[k])
            if key_length > 0 and key_length <= offset:
                seek = file_size - (key_length * int(offset/key_length))
                if seek > 0:
                    in_file.seek(seek)
                    keyChar = in_file.read(key_length)
                    while keyChar != '':
                        if keys[k] == keyChar:
                            if keys[k] not in charSetCheck:
                                charSetCheck[keys[k]] = 1
                            else:
                                charSetCheck[keys[k]] += 1
                        keyChar = in_file.read(key_length)
        debugCharSet(charSetCheck)
        keyCheckKeys = charSetCheck.keys()
        keyCheckValues = charSetCheck.values()
        return charSetCheck
    except Exception as e:
        print('Error:' + str(type(e)) + ':' + str(e) +
              ' at line: {}'.format(sys.exc_info()[-1].tb_lineno))


def findLongKey(charSet, keyStart, offset):
    keys = charSet.keys()
    values = charSet.values()
    kLen = len(keys) - 1
    mostMatches = 0
    longestKey = -1
    if int(file_size/offset) % 2 == 0:
        mod_factor = 2
    else:
        mod_factor = 1
    for k in range(kLen, -1, -1):
        len_key = len(keys[k])
        if len_key > len(keys[longestKey]) and len_key % mod_factor == 0:
            if values[k] >= int(file_size/offset):
                if file_size % len_key == 0:
                    longestKey = k
    return keys[longestKey]


def findRepeatKey(charSet, keyStart, offset):
    keys = charSet.keys()
    values = charSet.values()
    kLen = len(keys) - 1
    mostMatches = 0
    repeatKey = -1
    keyOut = ['']
    if int(file_size/offset) % 2 == 0:
        mod_factor = 2
    else:
        mod_factor = 1
    for k in range(kLen, -1, -1):
        len_key = len(keys[k])
        if (len_key >= 1 and len_key % mod_factor == 0):
            if values[k] > values[repeatKey]:
                if values[k] >= int(file_size/offset):
                    if file_size % len_key == 0:
                        repeatKey = k
    keyOut[0] = keys[repeatKey]
    return keyOut


def debugCharSet(charSet):
    if DEBUG is True:
        keys = charSet.keys()
        values = charSet.values()
        print keys
        print values
    else:
        return


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(
            prog='complexor', usage='%(prog)s [in-file] [out-file] [options]',
            description='XOR a file byte for byte based on'
                        ' string key and output the result.'
            )
        parser.add_argument('in_file', type=str, help='File input')
        parser.add_argument('out_file', type=str, help='File output')
        parser.add_argument(
            '-k', metavar='key', type=str,
            help='Specify a key rather than detect it automatically'
            )
        parser.add_argument(
            '-b', metavar='n', type=int,
            help='Number of Bytes to skip as offset'
            )
        parser.add_argument(
            '-w', metavar='bool', type=int, default=1,
            help='Write offset bytes [0=off, 1=on(default)]'
            )
        parser.add_argument(
            '-x', metavar='x', type=int, default=512,
            help='Detect the key using this offset from the end of file'
            )
        args = parser.parse_args()
        main(args)
    except Exception as e:
        sys.exit(0)
