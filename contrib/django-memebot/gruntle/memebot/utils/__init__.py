import sys

class DisableAutoTimestamps(object):

    def __init__(self, *models):
        self.models = models
        self.old_values = None

    def __enter__(self):
        self.old_values = {}
        for model in self.models:
            for field in model._meta.fields:
                try:
                    self.old_values[(model, field.name)] = field.auto_now_add, field.auto_now
                except AttributeError:
                    continue
                field.auto_now_add = field.auto_now = False
        return self

    def __exit__(self, *exc_info):
        for key, values in self.old_values.iteritems():
            model, field_name = key
            auto_now_add, auto_now = values
            for field in model._meta.fields:
                if field.name == field_name:
                    field.auto_now_add = auto_now_add
                    field.auto_now = auto_now
        self.old_values = None


def ipython(depth=0):
    """Embed IPython in running program"""
    from IPython.Shell import IPShellEmbed
    frame = sys._getframe(depth + 1)
    shell = IPShellEmbed(banner='Interactive mode, ^D to resume.', exit_msg='Resuming ...')
    shell(local_ns=frame.f_locals, global_ns=frame.f_globals)
