from collections import namedtuple

import mechanize
from django.contrib.auth.models import User

from bread.utils.urls import reverse_model

FormField = namedtuple("FormField", ["name", "value", "element", "generators"])


def authenticated(func):
    def wrapper(case, *args, **kwargs):
        user, _ = User.objects.get_or_create(username="admin", is_superuser=True)
        case.client.force_login(user)
        return func(case, *args, **kwargs)

    return wrapper


@authenticated
def generic_bread_test(case, model, **kwargs):
    """Creates a single object, calls browse, read and edit pages"""
    p = model(**kwargs)
    p.save()
    resp = case.client.get(reverse_model(model, "browse"))
    case.assertEqual(resp.status_code, 200)
    resp = case.client.get(reverse_model(model, "read", kwargs={"pk": p.pk}))
    case.assertEqual(resp.status_code, 200)
    test_form_page(case, reverse_model(model, "edit", kwargs={"pk": p.pk}))


def test_form_page(case, url, fuzzy_count=10):

    # find input-elements and create generators
    # ignore hidden, readonly and unusable fields
    # this function is likely the challenging part of the implementation
    url = f"{case.live_server_url}{url}"
    fields = extract_form(url)

    # save all fields unmodified and check save method works correctly
    initial_fieldvalues = {i.name: i.value for i in extract_form(url)}
    case.client.post(url, initial_fieldvalues)  # post without changes
    saved_fieldvalues = {i.name: i.value for i in extract_form(url)}
    assert initial_fieldvalues == saved_fieldvalues
    return

    # test mutations on all fields separately in a loop
    # more performant would be to modify many fields inside a single request
    # but it would less fine-grained and not reflect how most real-world edits happen
    for field in fields:
        # field.generators returns a list of tuples with a generator and a boolean is_valid_value
        # generator is a python generator which returns an infinite number of random values for the field
        # is_valid_value determines whether the generator generates valid values for the field or not
        for generator, is_valid_value in field.generators:
            for testvalue, _ in zip(generator, range(fuzzy_count)):
                case.client.post(url, {**initial_fieldvalues, field.name: testvalue})
                updated_fields = case.client.get(url)

                if is_valid_value:
                    assert updated_fields[field.name] == testvalue
                else:
                    assert updated_fields[field.name] == initial_fieldvalues[field.name]


def extract_form(url):
    br = mechanize.Browser()
    br.open(url)
    form = br.select_form(name="")
    print(form)

    return [FormField(name="", value="", element="", generators=[])]
