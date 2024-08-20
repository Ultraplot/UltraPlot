from contextlib import contextmanager


class WarningTracker:
    def __init__(self):
        self.warnings = []

    def __enter__(self):
        # This context manager captures warnings
        # It should initialize any state needed to capture warnings
        import warnings

        self._original_warning = warnings.showwarning
        warnings.showwarning = self._custom_showwarning
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        import warnings

        warnings.showwarning = self._original_warning

    def _custom_showwarning(
        self, message, category, filename, lineno, file=None, line=None
    ):
        self.warnings.append((message, category, filename, lineno, file, line))

    def __len__(self):
        return len(self.warnings)
