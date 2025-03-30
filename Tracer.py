from typing import Callable, Generator, Any
from collections import defaultdict
from time import perf_counter
from functools import wraps
from types import FrameType
from sys import setprofile


class Tracer:
    LOG_PREFIX = '[TRACE]'

    STATUS_TITLE = 'Trace Status'
    # STATUS_TITLE = None  # Set this variable to None to disable Status Title in the output

    STATUS_HEADERS = ('Function', 'Total Execution Time')
    # STATUS_HEADERS = None  # Set this variable to None to disable Status Headers in the output

    STATUS_NONE = 'No functions traced'
    PRECISION = 4

    def __init__(self, log=False):
        self._log_enabled = log

        self._traced_functions: set[str] = set()
        self._call_times = defaultdict(float)
        self._start_times = {}

        self.toggle()

    def _log(self, *messages: str):
        if self._log_enabled:
            print(f'{self.LOG_PREFIX}', *messages)

    @classmethod
    def _get_func_name(cls, func: Callable | str) -> str:
        return func if isinstance(func, str) else f'{func.__module__}.{func.__name__}'

    def toggle(self, *functions: Callable | str, **functions_kwargs: bool):
        for func in functions:
            func_name = self._get_func_name(func)
            functions_kwargs[func_name] = func_name not in self._traced_functions

        for func_name, should_trace in functions_kwargs.items():
            if should_trace:
                self._traced_functions.add(func_name)
            else:
                self._traced_functions.remove(func_name)
                self._start_times.pop(func_name, None)

        if self._traced_functions:
            self._log('Tracing functions:', *self._traced_functions)
            setprofile(self._trace_calls)
        else:
            setprofile(None)
            self._log('Tracing disabled')

    def enable(self, *functions: Callable | str, enable=True):
        self.toggle(*{self._get_func_name(func): enable for func in functions})

    def enable_all(self):
        self.enable(*self._traced_functions)

    def disable(self, *functions: Callable | str):
        self.enable(*functions, enable=False)

    def disable_all(self):
        self.disable(*self._traced_functions)

    def reset(self, *functions: Callable | str):
        for func in functions:
            self._call_times.pop(self._get_func_name(func), None)

    def __call__(self, func: Callable) -> Callable:
        self.enable(self._get_func_name(func))

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    def _trace_calls(self, frame: FrameType, event: str, arg: Any) -> Callable:
        if event == 'call':
            func_name = f'{frame.f_globals["__name__"]}.{frame.f_code.co_qualname}'
            # self._log(f'call: {func_name}')

            if func_name in self._traced_functions:
                end_time = perf_counter()
                self._start_times[frame] = end_time

        elif event == 'return':
            func_name = f'{frame.f_globals["__name__"]}.{frame.f_code.co_qualname}'
            # self._log(f'return: {func_name}')

            if func_name in self._traced_functions and frame in self._start_times:
                end_time = perf_counter()
                self._call_times[func_name] += end_time - self._start_times.pop(frame)

        return self._trace_calls

    @property
    def times(self) -> dict[str, float]:
        return self._call_times

    @property
    def time_sorted(self):
        if not self._call_times:
            return 'No functions traced'

        print('Function Execution Time (seconds):')
        print('----------------------------------')
        for func, duration in self._call_times.items():
            print(f'{func}: {duration:.6f}s')

    def _generate_string(self) -> Generator[str, None, None]:
        column_length = [0] * 2

        if self.STATUS_HEADERS:
            for index, header in enumerate(self.STATUS_HEADERS):
                column_length[index] = max(column_length[index], len(header))

        column_length[0] = max(column_length[0], max(map(len, self._call_times.keys()), default=0))
        column_length[1] = max(column_length[1], self.PRECISION + 3)
        total_length = sum(column_length) + len(column_length) * 3 + 1

        if self.STATUS_TITLE and total_length < len(self.STATUS_TITLE) + 4:
            column_length[0] += len(self.STATUS_TITLE) + 4 - total_length
            total_length = sum(column_length) + len(column_length) * 3 + 1

        if self.STATUS_TITLE:
            yield '┌' + '─' * (total_length - 2) + '┐'
            yield '│ ' + self.STATUS_TITLE.center(total_length - 4) + ' │'

        if not self._traced_functions:
            yield '├' + '─' * (total_length - 2) + '┤'
            yield '│ ' + self.STATUS_NONE.center(total_length - 4) + ' │'
            yield '└' + '─' * (total_length - 2) + '┘'

        else:
            yield ''.join((
                '├' if self.STATUS_TITLE else '┌',
                '─' * (column_length[0] + 2),
                '┬',
                '─' * (column_length[1] + 2),
                '┤' if self.STATUS_TITLE else '┐'
            ))

            if self.STATUS_HEADERS:
                yield f'│ {" │ ".join(
                    header.center(column_length[index]) for index, header in enumerate(self.STATUS_HEADERS)
                )} │'

                yield '├' + '─' * (column_length[0] + 2) + '┼' + '─' * (column_length[1] + 2) + '┤'

            for func, duration in self._call_times.items():
                yield ' '.join((
                    '│',
                    func.ljust(column_length[0]),
                    '→',
                    f'{duration:.{self.PRECISION}f}s'.center(column_length[1]),
                    '│'
                ))

            yield '└' + '─' * (column_length[0] + 2) + '┴' + '─' * (column_length[1] + 2) + '┘'

    def __str__(self) -> str:
        return '\n'.join(map(str.rstrip, self._generate_string()))
