def format_args(*args):
    """Format positional args as in a function call.

    E.g. ("foo", 42, {"k": "v"}) -> "'foo', 42, {'k': 'v'}".
    """
    return ", ".join(repr(arg) for arg in args)


def format_kwargs(**kwargs):
    """Format keyword args as in a function call.

    E.g. (number=42, d={"k": "v"}) -> 'number=42, d={'k': 'v'}'.
    """
    return ", ".join(
        f"{kwarg_name}={kwarg_value!r}" for kwarg_name, kwarg_value in kwargs.items()
    )


def format_args_kwargs(*args, **kwargs):
    """Format both positional and keyword args as in a function call."""
    args_str = format_args(*args)
    kwargs_str = format_kwargs(**kwargs)

    if kwargs_str:
        if args_str:
            args_str += ", "
        args_str += kwargs_str

    return args_str


def format_callable_call(callable_name, /, *args, **kwargs):
    """Format callable call as it could be written in a source code.

    E.g. ("random.sample", ['red', 'blue'], counts=[4, 2], k=5) ->
        'random.sample(['red', 'blue'], counts=[4, 2], k=5)'.
    """
    args_str = format_args_kwargs(*args, **kwargs)
    return f"{callable_name}({args_str})"
