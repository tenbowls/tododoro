def input_check(msg: str, v: list) -> None:
    '''Checks that user input is valid (i.e. is part of the list provided)'''
    ans = input(msg)
    while ans not in v:
        ans = input(msg)
    return ans 