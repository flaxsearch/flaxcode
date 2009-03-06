"""A simple utility that takes the name of a file and the name of a filter,
applies the filter to the file, and prints the results.

"""

import sys

sys.path.append('..')
sys.path.append('../indexserver')


def main():
    if len(sys.argv) != 3:
        print """ Usage: python runfilter <filtername> <filename> """
        return

    filtername, filename = sys.argv[1:]
    filter_module_name, filter_fun_name = filtername.rsplit('.',1)
    filter_module = __import__(filter_module_name)
    filter_fun = filter_module.__dict__[filter_fun_name]
    for chunk in filter_fun(filename):
        print chunk

if __name__ == "__main__":
    main()
