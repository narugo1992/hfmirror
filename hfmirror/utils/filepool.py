import os

from hbutils.random import random_sha1_with_timestamp
from hbutils.system import TemporaryDirectory, copy


class FilePool:
    def __init__(self):
        self.tmpdir = TemporaryDirectory()
        self.count = 0

    def __del__(self):
        self.tmpdir.cleanup()
        self.count = 0

    def put_file(self, path) -> str:
        tmppath = os.path.join(self.tmpdir.name, random_sha1_with_timestamp())
        os.makedirs(tmppath)

        dst_filename = os.path.join(tmppath, os.path.basename(os.path.abspath(path)))
        copy(path, dst_filename)

        self.count += 1
        return dst_filename

    def cleanup(self):
        self.tmpdir.cleanup()
        self.tmpdir = TemporaryDirectory()
        self.count = 0

    def __len__(self):
        return self.count
