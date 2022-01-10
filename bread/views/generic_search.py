import htmlgenerator as hg
from django.http import HttpResponse

from bread.utils import aslayout


@aslayout
def view(request):
    return HttpResponse("")


def script():
    return hg.SCRIPT(
        hg.mark_safe(
            """document.addEventListener('load', () => {
    let searchBox = document.querySelector('.bx--content .bx--search-input');
    let searchBoxClose = document.querySelector('.bx--content .bx--search-close');
    let currentURL = document.location.toString().split('?');
    let currentParams = {};
    if (currentURL.length > 1)
        currentURL[1].split('&').forEach(el => {
            [key, val] = el.split('=');
            val = decodeURIComponent(val);
            if (key === 'q') {
                searchBox.value = val;
                searchBoxClose.classList.remove('bx--search-close--hidden');
            }
            currentParams[key] = val;
        });
    searchBox.addEventListener('keydown', e => {
        if (e.code === 'Enter') {
            let boxVal = searchBox.value;
            currentParams['q'] = boxVal;
            let newQuery = [];
            for (let prop in currentParams)
                newQuery.push(encodeURI(prop + '=' + currentParams[prop]));
            document.location = currentURL[0] + '?' + newQuery.join('&');
        }
    });
    searchBoxClose.addEventListener('click', e => {
        document.location = document.location.href.split('?')[0] + '?reset=2';
    });
});"""
        )
    )
