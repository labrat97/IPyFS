import unittest
from random import random as rand
import subprocess as sp
from ipyfs import *
from math import sqrt
from typing import List


class ReadTest(unittest.TestCase):
    def testRandom(self):
        # Make sure both internal cat types are called to evaluate
        size:int = int(2.5*DEFAULT_IPFS_BLOCK_SIZE)

        # Generate random data to be retrieved
        tape = [None] * size
        for i in range(size):
            tape[i] = int(rand() * 255)
        proc = sp.Popen([DEFAULT_IPFS_COMMAND, 'add', '-Q', '--pin=false', '--stdin-name=12345'], stdin=sp.PIPE, stdout=sp.PIPE)
        hash = str.strip(proc.communicate(input=bytes(tape))[0].decode())
        offset:int = 0

        # Test the full file, including the sizing function
        with IPFile(hash, ipns=False) as file:
            self.assertEqual(len(bytes(tape)), file.__probeSize__())
            self.assertEquals(bytes(tape), file.read())

        # Test the file in chunks of prodided length
        with IPFile(hash, ipns=False) as file:
            for idx in [int(n*size/5) for n in range(5)]:
                self.assertEquals(bytes(tape[offset:idx+offset+1]), file.read(idx+1), msg=f'[{idx+1}]')
                offset += idx+1
                if offset >= size:
                    break
    
    def testRandomLines(self):
        # Generate random lines to seed the test
        lineCount:int = int((rand()+1)*sqrt(DEFAULT_IPFS_BLOCK_SIZE))
        lines:List[bytes] = []

        # Do generation math
        for _ in range(lineCount):
            # Make sure not too many blocks are generated
            length:int = int((rand()+1)*sqrt(DEFAULT_IPFS_BLOCK_SIZE))
            tape:List[int] = [0] * length

            # Add newlines during random generation when appropriate
            for idx in range(length):
                n = int(rand() * 255)
                while n == ord('\n'):
                    n = int(rand() * 255)
                tape[idx] = n
            lines.append(bytes(tape))
        # Now it's appropriate
        buffer:str = b'\n'.join(lines)

        # Add the file to IPFS, not pinning
        proc = sp.Popen([DEFAULT_IPFS_COMMAND, 'add', '-Q', '--pin=false'], stdin=sp.PIPE, stdout=sp.PIPE)
        hash = str.strip(proc.communicate(input=bytes(buffer))[0].decode())

        # Read and test the file by reading each line
        with IPFile(hash, ipns=False) as file:
            line = file.readline()
            idx:int = 0
            while not (line is None):
                self.assertEquals(bytes(lines[idx]), line, msg=f'[{idx+1}]')
                idx += 1
                line = file.readline()
