from time import sleep

from Tracer import Tracer


# You can turn the optional logs off here:
# tracer = Tracer(log=False)
tracer = Tracer(log=True)

# If no functions are traced yet, the tracer will print a nicely formatted message:
print(tracer)


# This demo showcases situations where functions can reside inside classes and other functions
# I've tried to make it as realistic as possible by including as many edge cases as I could think of :)

class SomeClass:  # No need to specify decorator for the class
    def __init__(self):
        pass

    @tracer(summ_recursive=True)
    def main_function(self, recursive: bool = True):
        """
        First run (recursive=True): 0.1s + {recursion}
        Second run: 0.3s
        Total time: {first run} + {second run} = (0.1s + 0.3s) + 0.3s = 0.7s
        """

        def inner_function_disabled():
            sleep(0.1)

        @tracer
        def inner_function():
            """
            For one `main_function` run: 0.1s
            For all `main_function` runs: 0.1s * 3 = 0.3s
            """
            sleep(0.1)

        sleep(0.1)

        if recursive:
            self.main_function(recursive=False)  # + 0.3s
        else:
            inner_function_disabled()  # + 0.1s
            inner_function()  # + 0.1s
            # inner_function_disabled()  # + 0.1s

    @tracer
    def toggled_function(self):
        """
        First run (enabled): 0.1s
        Second run (disabled): 0.1s
        Third run (enabled): 0.1s
        Total time: {first run} + {third run} = 0.1s + 0.1s = 0.2s
        """
        sleep(0.1)

    @classmethod
    def class_function(cls):
        """
        Only one run: 0.1s
        """
        sleep(0.1)

    def function_without_decorator(self):
        """
        Only one run: 0.1s
        """
        sleep(0.1)


class_instance = SomeClass()

class_instance.main_function()  # main_function: 0.7s, inner_function: 0.1s
class_instance.main_function()  # main_function: 0.7s, inner_function: 0.1s
class_instance.main_function()  # main_function: 0.7s, inner_function: 0.1s

# `setprofile` introduces some overhead but unlocks powerful capabilities.

# For instance, it allows enabling and disabling profiling for any function dynamically —
# just by referencing it — even if it wasn't originally decorated!

# Here's a showcase of various methods available in my class:
# toggle(*funcs), enable(*funcs), disable(*funcs), enable_all(), disable_all()

class_instance.toggled_function()  # toggled_function: 0.1s
tracer.disable(class_instance.toggled_function)
class_instance.toggled_function()
tracer.enable_all()
class_instance.toggled_function()  # toggled_function: 0.1s

tracer.toggle(class_instance.function_without_decorator)
class_instance.function_without_decorator()  # function_without_decorator: 0.1s
tracer.toggle(class_instance.function_without_decorator)

tracer.enable(SomeClass.class_function)
SomeClass.class_function()  # class_function: 0.1s
tracer.disable_all()

# Expected result:
# main_function: 2.1s
# toggled_function: 0.2s
# inner_function: 0.3s
# function_without_decorator: 0.1s
# class_function: 0.1s

print(tracer)
