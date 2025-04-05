from typing import Callable, Generator, Any
from types import FrameType, CodeType

from dataclasses import dataclass, field
from collections import defaultdict
from time import perf_counter
from functools import wraps
from sys import setprofile


@dataclass
class FunctionData:
    summ_recursive: bool = False
    runs: list[float] = field(default_factory=list)

    _start_times: list[float] = field(init=False, default_factory=list)
    _enabled: bool = field(init=False, default=True)

    def begin(self):
        self._start_times.append(perf_counter())

    def end(self):
        if not self._start_times:  # If reset happened during execution
            return

        start_time = self._start_times.pop()

        if self.summ_recursive or not self._start_times:
            self.runs.append(perf_counter() - start_time)

    @property
    def enabled(self):
        return self._enabled

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False
        self.start_times = []


def get_code(func: Callable):
    return func.__code__


def get_func_name(func: Callable) -> str:
    return func.__qualname__


def get_code_name(code: CodeType) -> str:
    return code.co_qualname


class Tracer:
    LOG_PREFIX = '[TRACER]'

    STATUS_TITLE = 'Trace Status'
    # STATUS_TITLE = None  # Set this variable to None to disable Status Title in the output

    STATUS_HEADERS = ('Function', 'Total Execution Time')
    # STATUS_HEADERS = None  # Set this variable to None to disable Status Headers in the output

    STATUS_NONE = 'No functions traced'
    PRECISION = 4

    def __init__(self, log: bool = False, use_setprofile: bool = False):
        self._log_enabled = log
        self._setprofile_watch: set[CodeType] = set()
        self._functions: dict[CodeType, FunctionData] = defaultdict(FunctionData)
        self._wrapper_mapping: dict[tuple[str, CodeType], CodeType] = {}

    def _log(self, *messages: str):
        if self._log_enabled:
            print(f'{self.LOG_PREFIX}', *messages)

    def reset(self):
        for code, func_data in self._functions.items():
            func_data.runs = []
            func_data.start_times = []
            self._log(f'Reset trace on "{get_code_name(code)}"')

    def toggle(self, *functions: Callable | CodeType, summ_recursive: bool = False, on: bool | None = None):
        for item in functions:
            if isinstance(item, CodeType):
                code = item
            else:
                code = get_code(item)
                code = self._wrapper_mapping.get((get_func_name(item), code), code)

            if on is not None:
                enable = on
            elif code not in self._functions:
                enable = True
            else:
                enable = not self._functions[code].enabled

            if enable:
                if code not in self._functions:
                    self._log(f'Enabling setprofile trace on "{get_code_name(code)}"')
                    self._setprofile_watch.add(code)
                else:
                    self._log(f'Enabling trace on "{get_code_name(code)}"')
                self._functions[code].enable()

            else:
                self._log(f'Disabling trace on "{get_code_name(code)}"')
                self._setprofile_watch.discard(code)
                self._functions[code].disable()

            self._functions[code].summ_recursive = summ_recursive

        if self._setprofile_watch:
            self._log('setprofile is enabled on the following functions:', *map(get_code_name, self._setprofile_watch))
            setprofile(self._trace_calls)
        else:
            setprofile(None)
            self._log('setprofile is temporary disabled')

    def enable(self, *functions: Callable | CodeType, summ_recursive: bool = False):
        self.toggle(*functions, summ_recursive=summ_recursive, on=True)

    def enable_all(self, summ_recursive: bool = False):
        self.enable(*self._functions, summ_recursive=summ_recursive)

    def disable(self, *functions: Callable | CodeType):
        self.toggle(*functions, on=False)

    def disable_all(self):
        self.disable(*self._functions)

    def __call__(self, wrapped_function: Callable | None = None, summ_recursive: bool = False) -> Callable:
        def decorator(func: Callable) -> Callable:
            code = get_code(func)

            @wraps(func)
            def wrapper(*args, **kwargs):
                # self._log(f'Entering {get_code_name(code)}')

                if not self._functions[code].enabled:
                    # self._log(f'Skipping {get_code_name(code)}')
                    return func(*args, **kwargs)

                self._functions[code].begin()
                result = func(*args, **kwargs)
                self._functions[code].end()

                # self._log(f'Exited {get_code_name(code)}')
                return result

            self._log(f'Enabling simple trace on "{get_code_name(code)}" due to decorator')
            self._wrapper_mapping[(get_func_name(func), get_code(wrapper))] = code
            self._functions[code].summ_recursive = summ_recursive

            return wrapper

        if wrapped_function is not None:
            return decorator(wrapped_function)

        return decorator

    def _trace_calls(self, frame: FrameType, event: str, arg: Any) -> Callable:
        if frame.f_code in self._setprofile_watch:
            if event == 'call':
                assert frame.f_code in self._functions, f'Broken internal invariant: setprofile-watch function ' \
                    f'{get_code_name(frame.f_code)} is not recognized'
                self._functions[frame.f_code].begin()

            elif event == 'return':
                assert frame.f_code in self._functions, f'Broken internal invariant: setprofile-watch function ' \
                    f'{get_code_name(frame.f_code)} is not recognized'
                self._functions[frame.f_code].end()

        return self._trace_calls

    @property
    def times(self) -> dict[str, float]:
        return {get_code_name(func): sum(data.runs) for func, data in self._functions.items()}

    def _generate_string(self) -> Generator[str, None, None]:
        column_length = [0] * 2

        if self.STATUS_HEADERS:
            for index, header in enumerate(self.STATUS_HEADERS):
                column_length[index] = max(column_length[index], len(header))

        column_length[0] = max(column_length[0], max(
            map(len, map(get_code_name, self._functions)), default=0
        ))
        column_length[1] = max(column_length[1], self.PRECISION + 3)
        total_length = sum(column_length) + len(column_length) * 3 + 1

        if self.STATUS_TITLE and total_length < len(self.STATUS_TITLE) + 4:
            column_length[0] += len(self.STATUS_TITLE) + 4 - total_length
            total_length = sum(column_length) + len(column_length) * 3 + 1

        if not self._functions:
            total_length = max(len(self.STATUS_NONE or '') + 4, len(self.STATUS_TITLE or '') + 4)

        if self.STATUS_TITLE:
            yield '┌' + '─' * (total_length - 2) + '┐'
            yield '│ ' + self.STATUS_TITLE.center(total_length - 4) + ' │'

        if not self._functions:
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

            for func, data in self._functions.items():
                yield ' '.join((
                    '│',
                    get_code_name(func).ljust(column_length[0]),
                    '→',
                    f'{sum(data.runs):.{self.PRECISION}f}s'.center(column_length[1]),
                    '│'
                ))

            yield '└' + '─' * (column_length[0] + 2) + '┴' + '─' * (column_length[1] + 2) + '┘'

    def __str__(self) -> str:
        return '\n'.join(self._generate_string())
