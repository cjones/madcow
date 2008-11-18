#!/usr/bin/env python

import sys
import megahal

def main():
    megahal.initbrain()
    print megahal.doreply('this is a test')
    return 0

if __name__ == '__main__':
    sys.exit(main())
