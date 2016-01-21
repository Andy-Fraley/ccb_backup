#!/usr/bin/env python

class tracelog:

    CONST_TRACE = ['Info', 'Warning', 'Error']
    trace_level = 'Info'
    print_level = 'Info'
    exit_level = 'Error'

    CONST_DETAIL = ['Low', 'High']
    detail_level = 'Low'

    def set_trace_level(self, str):
        assert str in self.CONST_LEVELS
        self.trace_level = str

    def get_trace_level(self):
        return self.trace_level

    def set_print_level(self, str):
        assert str in self.CONST_LEVELS
        self.print_level = str

    def get_print_level(self):
        return self.print_level

    def set_exit_level(self, str):
        assert str in self.CONST_LEVELS
        self.exit_level = str

    def get_exit_level(self):
        return self.exit_level

    def __init__(self, trace_level=None, print_level=None, exit_level=None):
        if trace_level is not None:
            self.set_trace_level(trace_level)
        if print_level is not None:
            self.set_print_level(print_level)
        if exit_level is not None:
            self.set_exit_level(exit_level)
