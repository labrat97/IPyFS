import unittest
from random import random as rand
import subprocess as sp
from main import *

IPFS_CMD = 'ipfs'

class ReversabilityTest(unittest.TestCase):
    def testRandom(self):
        # Make sure both internal cat types are called to evaluate
        size:int = int((rand()+1)*DEFAULT_IPFS_BUFFER_SIZE)

        # Generate random data to be retrieved
        tape = [None] * size
        for i in range(size):
            tape[i] = int(rand() * 255)
        proc = sp.Popen([IPFS_CMD, 'add', '-Q', '--pin=false'], stdin=sp.PIPE, stdout=sp.PIPE)
        hash = str.strip(proc.communicate(input=bytes(tape))[0].decode())
        offset:int = 0

        # Test the full file
        with IPFile(hash, ipns=False, command=IPFS_CMD) as file:
            self.assertEquals(bytes(tape), file.read())

        # Test the file in chunks of prodided length
        with IPFile(hash, ipns=False, command=IPFS_CMD) as file:
            for idx in [int(n*size/5) for n in range(5)]:
                self.assertEquals(bytes(tape[offset:idx+offset+1]), file.read(idx+1), msg=f'[{idx+1}]')
                offset += idx+1
                if offset >= size:
                    break
