import unittest
from random import random as rand
import subprocess as sp
from main import *
from typing import List

class SeekTest(unittest.TestCase):
    def __randInit(self) -> str:
        # Make sure both internal cat types are called to evaluate
        size:int = int((rand()+1)*DEFAULT_IPFS_BLOCK_SIZE)

        # Generate random data to be retrieved
        tape = [None] * size
        for i in range(size):
            tape[i] = int(rand() * 255)
        proc = sp.Popen([DEFAULT_IPFS_COMMAND, 'add', '-Q', '--pin=false'], stdin=sp.PIPE, stdout=sp.PIPE)
        hash = str.strip(proc.communicate(input=bytes(tape))[0].decode())

        return hash

    def testSeekCur(self):
        # Generate the random data to seek through
        mhash = self.__randInit()
        
        
