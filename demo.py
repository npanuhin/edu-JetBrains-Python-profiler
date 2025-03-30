from time import sleep

from Tracer import Tracer


tracer = Tracer(log=False)


@tracer
def small_function():
    sleep(0.1)


@tracer
def function_2():
    sleep(0.2)


small_function()  # First run: 0.1s total
small_function()  # Second run: 0.2s total

function_2()  # First run: 0.2s total

tracer.toggle(small_function)

# A couple runs to show that it's not being traced
small_function()
small_function()
small_function()

function_2()  # Second run: 0.4s total

tracer.toggle('__main__.small_function')

small_function()  # Third run: 0.3s total
small_function()  # Forth run: 0.4s total

print(tracer)  # Should print 0.4s for both function1 and function2
