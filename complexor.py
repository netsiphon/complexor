#!/usr/bin/env python


# complexor


import os
import sys
import argparse
from operator import xor


DEBUG = True
charset = {}
charset_check = {}
file_size = 0
max_key_size = 1024
load_types = 'filetypes.yml'


class FileTypes:
    def __init__(self):
        self.types = []
        self.type_lookup = {}


class FileType:
    def __init__(self):
        self.id = None
        self.file_magic = []
        self.file_magic_len = 0
        self.description = ""
        self.name = ""

MyTypes = FileTypes()

"""
    Main -
    in_file, out_file, key, offset, write_offset
"""


def main(args):
    try:
        pos = 0
        key_hint = ''
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
                if args.w:
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
                key_hint = check_head(in_file.read(2))
                if DEBUG:
                    print 'key_hint:"' + ''.join(key_hint) + '"'
                in_file.seek(file_size - detection_offset)
                charset = find_keys(in_file, key_hint, detection_offset)
                key = find_repeat_key(charset, key_hint, detection_offset)
                if DEBUG:
                    print 'RepeatedKey: ' + unicode(key)
                key = find_long_repeat_key(charset, key_hint, detection_offset)
                if DEBUG:
                    print 'Longestrepeat_key: ' + unicode(key)
                if key != '':
                    key = ''.join(key_hint) + key
                    print 'DETECT KEY: Found Key \'' + key + '\''
                else:
                    print('DETECT KEY: Failed to detect key! '
                          'Try a larger detection offset.')
        if key != '':
            # Key as array of characters
            bkey = list(key)
            key_len = len(key)
            in_file.seek(begin_offset)
            byte = ''
            byte = in_file.read(1)
            pos = 0
            while byte != '':
                key_cur = bkey[pos % key_len]
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


def check_head(first_chars):
    exe_head = ['M', 'Z', '0x90']
    key_start = ['', '', '']
    if DEBUG:
        print 'FirstChars:' + first_chars
    if len(first_chars) == 3:
        key_start[0] = chr(xor(ord(exe_head[0]), ord(first_chars[0])))
        key_start[1] = chr(xor(ord(exe_head[1]), ord(first_chars[1])))
        key_start[2] = chr(xor(ord(exe_head[2]), ord(first_chars[2])))
    return key_start


def check_file_header(fileType):
    file_head = ['M', 'Z', '0x90']
    key_start = ['', '', '']
    if DEBUG:
        print 'FirstChars:' + first_chars
    if len(first_chars) == 3:
        key_start[0] = chr(xor(ord(exe_head[0]), ord(first_chars[0])))
        key_start[1] = chr(xor(ord(exe_head[1]), ord(first_chars[1])))
        key_start[2] = chr(xor(ord(exe_head[2]), ord(first_chars[2])))
    return key_start
    

def find_keys(in_file, key_start, offset):
    try:
        file_size = os.path.getsize(args.in_file)
        key_char = in_file.read(1)
        key_buffer = ''
        key_buffer = key_buffer + key_char
        if int(file_size/offset) % 2 == 0:
            mod_factor = 2
        else:
            mod_factor = 1
        if DEBUG:
            print 'find_keys::ModFactor=' + str(mod_factor)
        in_file.seek(file_size - offset)
        while key_char != '':
            keyLen = len(key_buffer)
            if keyLen >= 3:
                if(key_buffer[keyLen - 3:] == ''.join(key_start) and keyLen %
                   mod_factor == 0):
                    # and file_size - (keyLen * int(offset/keyLen)) > 0:
                    key_buffer = ''
            if key_char in charset:
                charset[key_char] += 1
            else:
                charset[key_char] = 1
            if key_buffer in charset:
                charset[key_buffer] += 1
            else:
                charset[key_buffer] = 1
            key_char = in_file.read(1)
            key_buffer = key_buffer + key_char
        debug_charset(charset)
        keys = charset.keys()
        values = charset.values()
        klen = len(keys) - 1
        for k in range(klen, -1, -1):
            key_length = len(keys[k])
            if key_length > 0 and key_length <= offset:
                seek = file_size - (key_length * int(offset/key_length))
                if seek > 0:
                    in_file.seek(seek)
                    key_char = in_file.read(key_length)
                    while key_char != '':
                        if keys[k] == key_char:
                            if keys[k] not in charset_check:
                                charset_check[keys[k]] = 1
                            else:
                                charset_check[keys[k]] += 1
                        key_char = in_file.read(key_length)
        debug_charset(charset_check)
        key_check_keys = charset_check.keys()
        key_check_values = charset_check.values()
        return charset_check
    except Exception as e:
        print('Error:' + str(type(e)) + ':' + str(e) +
              ' at line: {}'.format(sys.exc_info()[-1].tb_lineno))


def find_long_key(charset, key_start, offset):
    keys = charset.keys()
    values = charset.values()
    klen = len(keys) - 1
    most_matches = 0
    longest_key = -1
    if int(file_size/offset) % 2 == 0:
        mod_factor = 2
    else:
        mod_factor = 1
    for k in range(klen, -1, -1):
        len_key = len(keys[k])
        if len_key > len(keys[longest_key]): # and len_key % mod_factor == 0:
            if values[k] >= int(file_size/offset):
                if file_size % len_key == 0:
                    longest_key = k
    return keys[longest_key]


def find_repeat_key(charset, key_start, offset):
    keys = charset.keys()
    values = charset.values()
    klen = len(keys) - 1
    most_matches = 0
    repeat_key = -1
    key_out = ['']
    if int(file_size/offset) % 2 == 0:
        mod_factor = 2
    else:
        mod_factor = 1
    for k in range(klen, -1, -1):
        len_key = len(keys[k])
        #if (len_key >= 1 and len_key % mod_factor == 0):
        if values[k] > values[repeat_key]:
            if values[k] >= int(file_size/offset):
                if file_size % len_key == 0:
                    repeat_key = k
    key_out[0] = keys[repeat_key]
    return key_out

def find_long_repeat_key(charset, key_start, offset):
    keys = charset.keys()
    values = charset.values()
    klen = len(keys) - 1
    most_matches = 0
    longest_key = -1
    repeat_key = -1
    if int(file_size/offset) % 2 == 0:
        mod_factor = 2
    else:
        mod_factor = 1
    for k in range(klen, -1, -1):
        len_key = len(keys[k])
        if len_key > len(keys[longest_key]):
            if values[k] > values[repeat_key]:
                if values[k] >= int(file_size/offset):
                    if file_size % len_key == 0 and repeat_key:
                        longest_key = k
                        repeat_key = k
    return keys[longest_key]
    
def debug_charset(charset):
    if DEBUG:
        keys = charset.keys()
        values = charset.values()
        klen = len(keys) - 1
        for k in range(klen, -1, -1):
            print 'Key: ' + keys[k] + ' -> ' + str(values[k]) + ';'
        print keys
        print values
    else:
        return

def load_file_types():
    try:
        file_types = open(load_types, 'rb')
    except:
        print 'Fatal Error: Could not open ' + load_types + '!'
        sys.exit(0)
    try:
        line = ''
        line = file_types.readline
        pos = 0
        while line != '':
            #YAML parsing here...
            
            line = file_types.readline
            pos += 1
        if DEBUG:
            print 'load_file_types::read: ' + str(pos) + ''
        file_types.close
    except:
        print 'Fatal Error Parsing ' + load_types + '!'
        sys.exit(0)
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
            '-t', metavar='type', type=str, default='pewin32',
            help='Specify a file type to use to detect the key (default=pewin32)'
            )
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
