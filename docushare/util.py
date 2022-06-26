from urllib.parse import urljoin

def join_url(*args):
    '''Construct a full URL by combining a base URL with other URLs.

    It is essentially a wrapper of :py:func:`urllib.parse.urljoin`. While :py:func:`urllib.parse.urljoin`
    accepts only two arguments, this wrapperfunction accepts multiple arguments to sequentially join the
    given items.

    Examples
    --------
    >>> join_url('https://www.example.com/', 'dir/', 'subdir/', 'filename.txt')
    'https://www.example.com/dir/subdir/filename.txt'

    >>> join_url('https://www.example.com/', 'dir/', 'subdir/', '/another_dir/' 'filename.bin')
    'https://www.example.com/another_dir/filename.bin'
    '''
    
    ret = None
    for arg in args:
        if ret is None:
            ret = arg
        else:
            ret = urljoin(ret, arg)
    return ret
