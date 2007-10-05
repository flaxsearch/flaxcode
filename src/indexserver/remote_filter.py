import subprocess
import sys
sys.path.append('..')
import util

class RemoteFilterRunner(object):
    """
    A filter that runs another filter in a subprocess.
    """

    def __init__(self, filter_name):
        'filter_name must be a string: "module.callable"'
        self.filter_name = filter_name
        self.server = None

    def __call__(self, file_name):
        self.maybe_start_server()
        self.io.send(file_name)
        while 1:
            block = self.io.receive()
            if block == "":
                break
            else:
                yield block

    def maybe_start_server(self):
        if not self.server:
            self.server = subprocess.Popen(['python', '-u', 'filterrunner.py', self.filter_name],
                                           stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            self.io = util.IO(instream = self.server.stdout, outstream = self.server.stdin)

# just for expermenting/testing
if __name__ == "__main__":
    filter = RemoteFilterRunner(sys.argv[1])
    while 1:
        filename = raw_input("Filename to filter: ")
        if filename == '0':
            break
        else:
            print "waiting for blocks...."
            for block in filter(filename):
                print block
            print "no more blocks."
    


