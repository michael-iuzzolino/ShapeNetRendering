import re
import struct

import numpy as np

__all__ = ['Obj', 'default_packer']
__version__ = '0.2.0'

RE_COMMENT = re.compile(r'#[^\n]*\n', flags=re.M)
RE_VERT = re.compile(r'^v\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)$')
RE_TEXT = re.compile(r'^vt\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)(?:\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?))?$')
RE_NORM = re.compile(r'^vn\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)\s+(-?\d+(?:\.\d+)?(?:[Ee]-?\d+)?)$')
RE_FACE = re.compile(r'^f\s+(\d+)(/(\d+)?(/(\d+))?)?\s+(\d+)(/(\d+)?(/(\d+))?)?\s+(\d+)(/(\d+)?(/(\d+))?)?$')

PACKER = 'lambda vx, vy, vz, tx, ty, tz, nx, ny, nz: struct.pack("%df", %s)'

def default_packer(vx, vy, vz, tx, ty, tz, nx, ny, nz):
    return struct.pack('9f', vx, vy, vz, tx, ty, tz, nx, ny, nz)


def int_or_none(x):
    return None if x is None else int(x)


def safe_float(x):
    return 0.0 if x is None else float(x)

class Obj:
    @staticmethod
    def open(filename) -> 'Obj':
        '''
            Args:
                filename (str): The filename.

            Returns:
                Obj: The object.

            Examples:

                .. code-block:: python

                    import ModernGL
                    from ModernGL.ext import obj

                    model = obj.Obj.open('box.obj')
        '''

        return Obj.fromstring(open(filename).read())

    @staticmethod
    def frombytes(data) -> 'Obj':
        '''
            Args:
                data (bytes): The obj file content.

            Returns:
                Obj: The object.

            Examples:

                .. code-block:: python

                    import ModernGL
                    from ModernGL.ext import obj

                    content = open('box.obj', 'rb').read()
                    model = obj.Obj.frombytes(content)
        '''

        return Obj.fromstring(data.decode())

    @staticmethod
    def fromstring(data) -> 'Obj':
        '''
            Args:
                data (str): The obj file content.

            Returns:
                Obj: The object.

            Examples:

                .. code-block:: python

                    import ModernGL
                    from ModernGL.ext import obj

                    content = open('box.obj').read()
                    model = obj.Obj.fromstring(content)
        '''

        vert = []
        text = []
        norm = []
        face = []

        data = RE_COMMENT.sub('\n', data)

        for line in data.splitlines():
            line = line.strip()

            if not line:
                continue

            match = RE_VERT.match(line)

            if match:
                vert.append(tuple(map(safe_float, match.groups())))
                continue

            match = RE_TEXT.match(line)
            if match:
                text.append(tuple(map(safe_float, match.groups())))
                continue

            match = RE_NORM.match(line)

            if match:
                norm.append(tuple(map(safe_float, match.groups())))
                continue

            match = RE_FACE.match(line)

            if match:
                v, t, n = match.group(1, 3, 5)
                face.append((int(v), int_or_none(t), int_or_none(n)))
                v, t, n = match.group(6, 8, 10)
                face.append((int(v), int_or_none(t), int_or_none(n)))
                v, t, n = match.group(11, 13, 15)
                face.append((int(v), int_or_none(t), int_or_none(n)))
                continue


        if not face:
            raise Exception('empty')


        t0, n0 = face[0][1:3]

        for v, t, n in face:
            # if (t0 is None) ^ (t is None):
            #     print("t0 is None: {}".format(t0 is None))
            #     print("t is None: {}".format(t is None))
            #     print("\n\n")
            #     print(v, t, n)
            #     print("\n\n")
            #
            #     raise Exception('INCONSISTENT')

            if (n0 is None) ^ (n is None):
                # print("n0 is None: {}".format(n0 is None))
                # print("n is None: {}".format(n is None))
                # print("\n\n")
                # print(v, t, n)
                # print("\n\n")

                raise Exception('INCONSISTENT')


        return Obj(vert, text, norm, face)

    def __init__(self, vert, text, norm, face):
        self.vert = vert
        self.text = text
        self.norm = norm
        self.face = face

    def pack(self, packer=default_packer) -> bytes:
        '''
            Args:
                packer (str or lambda): The vertex attributes to pack.

            Returns:
                bytes: The packed vertex data.

            Examples:

                .. code-block:: python

                    import ModernGL
                    from ModernGL.ext import obj

                    model = obj.Obj.open('box.obj')

                    # default packer
                    data = model.pack()

                    # same as the default packer
                    data = model.pack('vx vy vz tx ty tz nx ny nz')

                    # pack vertices
                    data = model.pack('vx vy vz')

                    # pack vertices and texture coordinates (xy)
                    data = model.pack('vx vy vz tx ty')

                    # pack vertices and normals
                    data = model.pack('vx vy vz nx ny nz')

                    # pack vertices with padding
                    data = model.pack('vx vy vz 0.0')
        '''

        if isinstance(packer, str):
            nodes = packer.split()
            packer = eval(PACKER % (len(nodes), ', '.join(nodes)))

        result = bytearray()

        for v, t, n in self.face:
            vx, vy, vz = self.vert[v - 1]
            try:
                tx, ty, tz = self.text[t - 1] if t is not None else (0.0, 0.0, 0.0)
            except:
                tx, ty, tz = 0.0, 0.0, 0.0
            nx, ny, nz = self.norm[n - 1] if n is not None else (0.0, 0.0, 0.0)
            result += packer(vx, vy, vz, tx, ty, tz, nx, ny, nz)

        return bytes(result)

    def to_array(self) -> np.array:
        return np.array([
            [
                *(self.vert[v - 1]),
                *(self.norm[n - 1] if n is not None else (0.0, 0.0, 0.0)),
                *(self.text[t - 1] if t is not None else (0.0, 0.0, 0.0)),
            ]
            for v, t, n in self.face
        ], dtype='f4')
