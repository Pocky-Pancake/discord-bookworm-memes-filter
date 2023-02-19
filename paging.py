from math import ceil
from typing import Union

def mkpages(iterable:Union[list,str,tuple,dict,set], items:int):
    pages = []
    items = 1 if items <= 0 else items
    for x in iterable:
        page = 0
        appending = True
        while appending:
            try:
                if len(pages[page]) < items:
                    pages[page].append(x)
                    appending = False
                else:
                    page += 1
            except:
                pages.append([x])
                appending = False
    return tuple(pages)