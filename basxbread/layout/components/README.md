Progress of components implementation
-------------------------------------

NOTE FOR DEVELOPERS:
The form components do currently use a rather suboptimal implementation where a lot of work is done inside the render method and only working when used inside django generated forms (but not as standalone elements).
The clean way would be to do everything inside __init__ and use lazy evaluation from htmlgenerator.
Please check the implementation of Select in select.py for how to do it right.
The other form elements should be implemented the same way.

Grids and icons are already implemented as well.

High prio:
- [x] Button: button.py
- [x] Checkbox: checkbox.py
- [x] Data table: datatable.py needs pagination and sorting added
- [x] Date picker: date_picker.py
- [ ] Dropdown: 
- [x] File uploader: 
- [x] Form: form.py
- [x] Modal: modal.py
- [x] Multiselect: 
- [x] Notification: notification.py
- [ ] Number input: 
- [x] Pagination: 
- [/] Progress indicator: progress_indicator.py
- [x] Overflow menu: overflow_menu.py
- [ ] Radio button: 
- [x] Search: search.py
- [x] Select: select.py
- [ ] Slider: 
- [x] Tabs: tabs.py
- [x] Tag: 
- [x] Text input: text_area.py, text_input.py
- [ ] Tile: 
- [x] Toggle: toggle.py
- [ ] Tooltip: 

Low prio:
- [ ] Accordion
- [x] Content switcher
- [ ] Link
- [ ] List
- [ ] Loading
- [ ] Structured list
- [ ] Inline loading: 
- [ ] UI shell
- [ ] Breadcrumb
- [ ] Code snippet
