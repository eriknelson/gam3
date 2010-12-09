from pygame.image import load

import sys

s = load(sys.argv[1])
t = file(sys.argv[2], 'w')

for y in range(s.get_height()):
    for x in range(s.get_width()):
        v = s.get_at((x, y))[0]
        if v < 64:
            ch = 'W'
        elif v < 92:
            ch = 'D'
        elif v < 192:
            ch = 'G'
        else:
            ch = 'M'
        t.write(ch)
    t.write('\n')
t.close()
