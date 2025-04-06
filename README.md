<h1 align="center">Python execution time tracer</h1>

This project features a Python class designed to measure the execution time of arbitrary Python functions. It offers flexible interfaces for specifying which functions to trace and for managing the tracing process — all while maintaining relatively low runtime overhead.

The repository includes a built-in demo that highlights the core functionality of the tracer (see details below) and also doubles as a basic test suite.


## Features

- Flexible interfaces for specifying which functions to trace — several convenient options are available (see below for details)
- Rich set of runtime controls — dynamically add or remove functions, start or stop tracing, and print results at any point during execution
- Zero\* overhead when tracing is disabled — no performance impact

\**Minimal constant overhead only when using decorators; see the explanation below*


## Usage

A function can be traced in two ways:

1) Using the `@tracer` decorator

    This wraps the target function with a lightweight wrapper that introduces minimal constant overhead. It's a simple and efficient option when tracing needs are known in advance.

2) Passing a function reference to `toggle()` or `enable()`

    This method offers maximum flexibility: you can dynamically enable tracing for any function during runtime. No need to predefine decorators — just pass a reference and you're good to go!

    Note, however, that this method introduces some runtime overhead. This is because it relies on Python's built-in [`sys.setprofile()`](https://docs.python.org/3/library/sys.html#sys.setprofile) function, which monitors every function call throughout the program. By default, `setprofile` is disabled unless at least one function is traced without using a decorator. Once `setprofile` is activated, you can trace any number of functions. While the overhead remains significant, it does not increase as you add more functions. `setprofile` will be automatically disabled when you stop tracing non-decorated functions.


Both approaches work seamlessly with nested functions, instance methods, and class methods. Enabling or disabling tracing for any function is as simple as calling one of the following methods:

```python
tracer.toggle(*function_references)   # Switch tracing on/off for given functions

tracer.enable()                       # Enables tracing for all functions
tracer.enable(*function_references)   # Enables tracing for given functions

tracer.disable()                      # Disables tracing for all functions
tracer.disable(*function_references)  # Disables tracing for given functions

tracer.reset()                        # Clears all recoded data for all functions
tracer.reset(*function_references)    # Clears all recoded data for given functions
```

For the output format I implemented a simple sum of all calls for each function, accessible both programmatically and in human-readable format. The output data can be extended depending on the need in the future.

I've also included a handy feature for recursive functions: you can choose whether to calculate the total time by summing every recursive call or by counting only the outermost ones. This behavior can be toggled using the `sum_recursive=True/False` argument, available in both the decorator and the `toggle/enable` methods.

```python
print(tracer.times)  # Machine-readable dictionary  {function_name: sum_of_times}

print(tracer)        # Human-readable table:
┌────────────────────────────────────────────────────────────────────────┐
│                              Trace Status                              │
├─────────────────────────────────────────────────┬──────────────────────┤
│                     Function                    │ Total Execution Time │
├─────────────────────────────────────────────────┼──────────────────────┤
│ SomeClass.main_function                         →       2.1208s        │
│ SomeClass.toggled_function                      →       0.2021s        │
│ SomeClass.main_function.<locals>.inner_function →       0.3027s        │
│ SomeClass.function_without_decorator            →       0.1015s        │
│ SomeClass.class_function                        →       0.1006s        │
└─────────────────────────────────────────────────┴──────────────────────┘
```


## Demo

As mentioned earlier, this repository includes a built-in demo file with comments that highlight the core functionality of the tracer, while also serving as a basic test suite.

For a detailed showcase of the tracer's interface and features, please refer to the [`demo.py`](demo.py) file. 😊


## Technical details & Testing

The tracing utility is implemented in Python 3 (tested with 3.13) and relies solely on the standard library, ensuring maximum portability and zero external dependencies.

Code quality is ensured through:
- `flake8` (with multiple plugins) — the most common linter for Python
- `mypy` — a static type checker enforcing strong typing

These code quality checks are automatically run via GitHub Actions on each push: <a href="https://github.com/npanuhin/edu-JetBrains-Python-profiler/actions"><img src="https://github.com/npanuhin/edu-JetBrains-Python-profiler/actions/workflows/python-lint.yml/badge.svg"></a>
