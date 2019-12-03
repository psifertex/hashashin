#!/usr/bin/env python3

# Copyright 2019 River Loop Security LLC, All Rights Reserved
# Author Rylan O'Connell

import os
import sys
import argparse
from typing import Tuple

import binaryninja as binja
from lsh import hash_all
from parsing import read_json
from tagging import tag_function
from annotations import Annotations


def apply(binary_path: str, sig_path: str) -> Tuple[int, str]:
    """
    Applies signatures in specified file to specified binary, and writes resulting bndb to disk

    :param binary_path: path of binary to apply signatures to
    :param sig_path: path of signature file to read in
    :return: tuple (int count of function signatures matched, str path to BNDB with tags that was created)
    """
    bv = binja.BinaryViewType.get_view_of_file(binary_path)
    print("Loaded binary {} into Binary Ninja.".format(binary_path))
    functions = hash_all(bv)
    print("{} functions in binary have been hashed.".format(len(functions)))
    data = read_json(sig_path)
    signatures = {}
    for raw_hash in data:
        # only bother with functions that actually have tags
        if len(data[raw_hash]) > 0:
            signatures[raw_hash] = Annotations(raw_data=data[raw_hash])

    print("Signature file {} loaded into memory.".format(sig_path))

    num_func_sigs_applied = 0
    for function_hash in functions:
        if function_hash in signatures:
            tag_function(bv, functions[function_hash], function_hash, signatures)
            print('Located a match at {}!'.format(function_hash))
            num_func_sigs_applied += 1

    output_bndb = os.path.join(os.getcwd(), binary_path + '.bndb')
    print("Writing output Binary Ninja database at {}".format(output_bndb))
    bv.create_database(output_bndb)
    return num_func_sigs_applied, output_bndb


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Apply signatures that were captured from a signature file to a binary.')
    parser.add_argument('binary', type=str,
                        help='The executable file to attempt to apply signatures onto.')
    parser.add_argument('signature_file', type=str,
                        help='The JSON signature file generated by `generate_signatures.py`.')
    args = parser.parse_args()

    if not os.path.isfile(args.binary):
        print("Must provide valid path to binary.")
        sys.exit(-1)
    if not os.path.isfile(args.signature_file):
        print("Must provide valid path to signature_file.")
        sys.exit(-2)

    apply(args.binary, args.signature_file)
