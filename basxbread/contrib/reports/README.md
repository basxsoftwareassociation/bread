BasxBread Reports
=============

This module adds report objects to an application.
Reports can be configured directly in the UI by defining columns with accessor-attributes and a djanglql filter (see <https://github.com/ivelum/djangoql/>).
Since djangoql only covers simpler query logic, it is possible to use define filters in a Python function.
Custom defined filters need to be registered via django settings in the variable ```REPORT_FILTERS```.
```REPORT_FILTERS``` must be of type dict. The keys of ```REPORT_FILTERS``` will show up in the UI in order to select a certain filter for a report. The values of ```REPORT_FILTERS``` must be functions which take the report model as argument and return a queryset.
The returned queryset must return objects of the same type as the report model.

Example:

    def birthday_today(model):
        import datetime
        return model.objects.filter(date_of_birth=datetime.date.today())

    REPORT_FILTERS = {
        "Is Adult": lambda model: model.objects.filter(age >= 18)
        "Birthday Today": birthday_today
    }

