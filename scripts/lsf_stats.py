
short_stats = [
    'exit_code',
    'cpu_time',
    'wall_clock_time',
    'max_memory',
    'requested_memory'
]

date_time_match_string = '(at|on)\s+[a-zA-Z]+\s+([a-zA-Z]+)\s+([0-9]+)\s+([0-9]{2}):([0-9]{2}):([0-9]{2})\s+([0-9]{4})$'
regexes = {
    'exec_host': re.compile('^Job was executed on host\(s\) <(.*)>, in queue <.*>, as user <.*> in cluster <.*>.$'),
    'working_dir': re.compile('^<(.*)> was used as the working directory.$'),
    'exit_code': re.compile('(^Successfully completed\.$)|(?:^Exited with exit code ([0-9]+)\.$)'),
    'cpu_time': re.compile('^\s+CPU time\s+:\s+([0-9]+\.[0-9]+) sec.$'),
    'max_memory': re.compile('^\s+Max Memory\s+:\s+([0-9]+) MB$'),
    'requested_memory': re.compile('^\s+Total Requested Memory\s+:\s+([0-9]+\.[0-9]+) MB'),
    'max_processes': re.compile('^\s+Max Processes\s+:\s+([0-9]+)$'),
    'max_threads': re.compile('^\s+Max Threads\s+:\s+([0-9]+)$'),
    'start_time': re.compile('^Started ' + date_time_match_string),
    'end_time': re.compile('^Results reported ' + date_time_match_string)
}

"""with open(property_file) as f:
    lines = f.readlines()
"""

class Stats:
    '''A class for getting stats from an lsf output file. E.g. memory, CPU usage etc'''
    def __init__(self, file):
        for stat in short_stats:
            exec('self.' + stat + ' = None')
        self.file= file


    def __eq__(self, other):
        return type(other) is type(self) and self.__dict__ == other.__dict__

    def readoutfile(self):
        with open(self.file) as f:
            lines = f.readlines().rstrip()
            for line in lines:
                hits = regexes[exit_code].search(line)
                if hits is None:
                    pass
                elif hits.group(1) is not None:
                    self.exit_code = 0
                elif hits.group(2) is not None:
                    self.exit_code = int(hits.group(2))



