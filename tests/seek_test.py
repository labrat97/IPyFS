import unittest
from random import random as rand
from random import randint
import subprocess as sp
from ipyfs import *

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

    def testSeek(self):
        # Generate the random data to seek through
        mhash = self.__randInit()
        
        # Keep track of the seek position
        vpos:int = 0
        file = IPFile(mhash, ipns=False)
        while not file.eof:
            self.assertEqual(file.tell(), vpos)

            offset = randint(DEFAULT_IPFS_BLOCK_SIZE/16, DEFAULT_IPFS_BLOCK_SIZE/2)
            curpos = file.seek(offset, SEEK_CUR)
            setpos = file.seek(offset+vpos, SEEK_SET)
            filesize = file.__probeSize__()
            endpos = file.seek((-filesize)+vpos+offset, SEEK_END)

            self.assertEqual(curpos, setpos, msg=f'offset: {offset}\tvpos: {vpos}')
            self.assertEqual(curpos, endpos, msg=f'offset: {offset}\tvpos: {vpos}')
            vpos += offset
