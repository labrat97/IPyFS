from argparse import ArgumentError
import subprocess as sp
from io import TextIOBase, SEEK_SET, SEEK_CUR, SEEK_END
from os import environ

import cid

DEFAULT_IPFS_BLOCK_SIZE:int = 256 * int(2**10) # 256k -> The default IPFS chunker size
DEFAULT_IPFS_COMMAND:str = environ.get('IPYFS_CMD', 'ipfs')
SUCCESS:int = 0
FAILURE:int = 1

class IPFile(TextIOBase):
    def __init__(self, multihash:str, ipns:bool=False, command:str=DEFAULT_IPFS_COMMAND, blockSize:int=DEFAULT_IPFS_BLOCK_SIZE):
        super(IPFile, self).__init__()

        # Make sure the provided cid is valid
        if not cid.is_cid(multihash):
            raise ArgumentError(f'\"{multihash}\" is not a valid content identifier.')
        self.multihash:str = multihash

        # Basic running parameters
        self.command:str = command
        self.ipns:bool = ipns
        # Not using path.sep as ipfs has a well defined sep
        self.ippath:str = f"/{'ipns' if self.ipns else 'ipfs'}/{self.multihash}"
        self.curpos:int = 0
        self.eof:bool = False
        self.seekbuf:int = blockSize

        # Hold the process that runs the shell command
        self.lastproc:sp.Popen = None

    def __waitForLast(self):
        # Wait for the self contianed process to end
        if self.lastproc is None: return
        assert self.lastproc.wait() == SUCCESS
        self.lastproc = None

    def read(self, size:int=-1) -> bytes:
        # Quick return, at end of the file
        if self.eof or size == 0: return None

        # Wait for the last process call to finish if it was non-blocking
        self.__waitForLast()

        # Start the process to pull the data from ipfs, then pull the data into python
        args = [self.command, 'cat', '-o', str(self.curpos)]
        if size >= 0:
            args.extend(['-l', str(size)])
        args.append(self.ippath)
        self.lastproc = sp.Popen(args, stdout=sp.PIPE, stderr=sp.PIPE)
        stdout, _ = self.lastproc.communicate()
        outlen = len(stdout)
        self.lastproc = None

        # Increment cursor
        if (not self.eof) and size >= 0:
            self.curpos += size
            if outlen < size:
                self.eof = True
            return stdout[:size]
        return stdout
    
    def readline(self, size:int=-1) -> bytes:
        # Quick return, at the end of the file
        if self.eof: return None

        # Wait for the last process call to finish if it was non-blocking
        self.__waitForLast()

        # Some running data
        aggregator = []
        searching:bool = True
        newlineIdx:int = -1

        # Filter the size argument for the method
        if size < 0 or size > self.seekbuf:
            batchsize:int = self.seekbuf
        else:
            batchsize:int = size

        # Scan the read for newlines, ending early if a newline is found
        while searching:
            buffer:bytes = self.read(batchsize)
            aggregator.append(buffer)
            newlineIdx = buffer.find(b'\n')
            searching = (newlineIdx < 0) and not self.eof

        # Trim off the unneeded tail of the buffer
        if newlineIdx > 0:
            self.curpos = (self.curpos - len(aggregator[-1])) + newlineIdx + 1
            aggregator[-1] = aggregator[-1][:newlineIdx]
        elif newlineIdx == 0:
            aggregator = aggregator[:-1]
        
        return b''.join(aggregator)

    def tell(self) -> int:
        if self.eof: return None
        return self.curpos
    
    def seek(self, offset:int, whence:int=SEEK_CUR):
        if whence == SEEK_CUR:
            return self.curpos
        elif whence == SEEK_END:
            self.eof = True
            self.curpos = -1
        elif whence == SEEK_SET:
            if self.curpos == -1 or (self.curpos != -1 and offset < self.curpos):
                self.eof = False
                self.curpos = offset
        else:
            raise ArgumentError(whence, f'Unknown literal provided: \"{whence}\"')
        
        return self.curpos
