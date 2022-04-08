
// support onload after page loaded for all elements
document.addEventListener(
    "DOMContentLoaded",
    () => bread_load_elements()
);

// same for ajax content
htmx.onLoad(function(content) {
    bread_load_elements();
});

function bread_load_elements() {
    $$('[onload]:not(body):not(frame):not(iframe):not(img):not(link):not(script):not(style)')._.fire("load")
}

// make sure to display content from faild ajax requests
htmx.on('htmx:responseError', function(event) {
    console.log(event);
    event.detail.target.innerHTML = event.detail.xhr.responseText;
});

// some helper which are used for the multiselect widget
function updateMultiselect(e) {
    let elem = $('.bx--list-box__selection', e);
    if (elem) {
        elem.firstChild.textContent = $$('fieldset input[type=checkbox][checked]', e).length;
    }
}

function filterOptions(e) {
    var searchterm = $('input.bx--text-input', e).value.toLowerCase()
    for(i of $$('fieldset .bx--list-box__menu-item', e)) {
        if (i.innerText.toLowerCase().includes(searchterm)) {
            $(i)._.style({display: "initial"});
        } else {
            $(i)._.style({display: "none"});
        }
    }
}

function clearMultiselect(e) {
    for(i of $$('fieldset input[type=checkbox][checked]', e)) {
        i.parentElement.setAttribute("data-contained-checkbox-state", "false");
        i.removeAttribute("checked");
        i.removeAttribute("aria-checked");
    }
    updateMultiselect(e);
}

// function which make the django inline-formset mechanism work dynamically
function init_formset(form_prefix) {
    update_add_button(form_prefix);
}

function delete_inline_element(checkbox, element) {
    checkbox.checked = true;
    element.style.display = "none";
}

function update_add_button(form_prefix) {
    var formcount = $('#id_' + form_prefix + '-TOTAL_FORMS');
    var maxforms = $('#id_' + form_prefix + '-MAX_NUM_FORMS');
    var addbutton = $('#add_' + form_prefix + '_button');
    if(addbutton) {
        addbutton.style.display = "inline-flex";
        if(parseInt(formcount.value) >= parseInt(maxforms.value)) {
            addbutton.style.display = "none";
        }
    }
}

function formset_add(form_prefix, list_container) {
    let container_elem = $(list_container);

    // some magic to add a new form element, copied from template empty_XXX_form
    // DOMParser.parseFromString does not work because it create a valid DOM document but we work with DOM elements
    let placeholder = document.createElement("DIV");
    container_elem.appendChild(placeholder);
    var formcount = $('#id_' + form_prefix + '-TOTAL_FORMS')
    var newElementStr = $('#empty_' + form_prefix + '_form').innerText.replace(/__prefix__/g, formcount.value)
    placeholder.outerHTML = newElementStr;

    formcount.value = parseInt(formcount.value) + 1;
    update_add_button(form_prefix);
    updateMultiselect(container_elem);

    bread_load_elements();
    htmx.process(container_elem);
}

// Function which is used to collect checkboxes from a datatable and submit the selected checkboxes to a URL for bulk processing
function submitbulkaction(table, actionurl, method="GET") {
    let form = document.createElement("form");
    form.method = method;
    form.action = actionurl;

    // make sure query parameters of the URL are passed as well (necessary for filters)
    let url = new URL(actionurl, new URL(document.baseURI).origin);
    for (const [key, value] of url.searchParams) {
        let input = document.createElement("input");
        input.name = key;
        input.type = "hidden";
        input.value = value;
        form.appendChild(input);
    }

    for(let checkbox of table.querySelectorAll('input[type=checkbox][data-event=select]')) {
        form.appendChild(checkbox.cloneNode(true));
    }

    for(let checkbox of table.querySelectorAll('input[type=checkbox][data-event=select-all]')) {
        form.appendChild(checkbox.cloneNode(true));
    }

    document.body.appendChild(form);
    form.submit();
}

// helper functions to set and get bread-namespaced cookies
function setBreadCookie(key, value) {
    document.cookie = "bread-" + key + "=" + encodeURIComponent(value) + "; path=/";
}

function getBreadCookie(key, _default=null) {
    var ret = document.cookie.split('; ').find(row => row.startsWith("bread-" + key + '='))
    if(!ret)
        return _default;
    ret = ret.split('=')[1];
    return ret ? decodeURIComponent(ret) : _default;
}

// js code for menu picker
function menuPickerLabel(target) {
    return target.querySelector("label");
}
function setMenuPickerChecked(target, value) {
    const label = menuPickerLabel(target);
    label.setAttribute("data-contained-checkbox-state", value.toString())
    label.firstChild.checked = value === true || value === "mixed";
    label.firstChild.setAttribute("aria-checked", value.toString())
}

const setMenuPickerSelectAllChecked = (target, value) => {
    const selectallTarget = target.closest(".bread--menupicker__table").querySelector(".bread--menupicker__selectall");
    setMenuPickerChecked(selectallTarget, value);
};

const menuPickerAdd = (target, event) => {
    const datatable = target.closest(".bread--menupicker");
    const selectedRowsTable = datatable.querySelector(".bread--menupicker__selected-table tbody")
    const unselectedRowsTable = datatable.querySelector(".bread--menupicker__unselected-table tbody")
    const unselectedRows = [...datatable.querySelectorAll(".bread--menupicker__unselected-table tbody tr")];

    // browse all checked rows
    const checkedUnselected = unselectedRows.filter(
        el => menuPickerLabel(el).getAttribute("data-contained-checkbox-state") === "true"
    );

    // move the checked rows to the left, in the preserved order.
    if (checkedUnselected.length > 0) {
        setMenuPickerSelectAllChecked(unselectedRowsTable, false);
        selectedRowsTable.append(...checkedUnselected);
        checkedUnselected.forEach(el => {
            const checkbox = menuPickerLabel(el).firstChild;
            const inputTag = document.createElement("input");
            inputTag.setAttribute("type", "hidden");
            inputTag.setAttribute("name", checkbox.getAttribute("data-name"));
            inputTag.setAttribute("value", checkbox.getAttribute("data-value"));
            datatable.appendChild(inputTag);
        });
        [...selectedRowsTable.children]
            .sort((a, b) =>
                parseInt(a.firstChild.getAttribute("data-order"))
                - parseInt(b.firstChild.getAttribute("data-order"))
            )
            .forEach(el => {
                setMenuPickerChecked(el, false);
                selectedRowsTable.appendChild(el);
            });
    }
};
const menuPickerRemove = (target, event) => {
    const datatable = target.closest(".bread--menupicker");
    const selectedRowsTable = datatable.querySelector(".bread--menupicker__selected-table tbody")
    const unselectedRowsTable = datatable.querySelector(".bread--menupicker__unselected-table tbody");
    const selectedRows = [...datatable.querySelectorAll(".bread--menupicker__selected-table tbody tr")];

    // browse all checked rows
    const checkedSelected = selectedRows.filter(
        el => menuPickerLabel(el).getAttribute("data-contained-checkbox-state") === "true"
    );

    // move the checked rows to the right, in the preserved order.
    if (checkedSelected.length > 0) {
        setMenuPickerSelectAllChecked(selectedRowsTable, false);
        unselectedRowsTable.append(...checkedSelected);
        checkedSelected.forEach(el => {
            const checkbox = menuPickerLabel(el).firstChild;
            const inputHidden = datatable.querySelector(`input[type="hidden"][name="${checkbox.getAttribute('data-name')}"][value="${checkbox.getAttribute('data-value')}"]`);
            console.log(inputHidden);
            console.log(datatable);
            datatable.removeChild(inputHidden);
        });
        [...unselectedRowsTable.children]
            .sort((a, b) =>
                parseInt(a.firstChild.getAttribute("data-order"))
                - parseInt(b.firstChild.getAttribute("data-order"))
            )
            .forEach(el => {
                setMenuPickerChecked(el, false);
                unselectedRowsTable.appendChild(el);
            });
    }
};

const menuPickerSelectAllClick = (target, event) => {
    const rows = [...target.closest(".bread--menupicker__table").querySelectorAll("tbody tr")];
    const checked = target.checked;

    rows.forEach(row => setMenuPickerChecked(row, checked));
};


const menuPickerCheckPerformed = (target, event) => {
    const table = target.closest(".bread--menupicker__table");
    const tableRows = [...table.querySelectorAll("tbody tr")];
    const tableRowsChecked = tableRows.filter(row => menuPickerLabel(row).firstChild.checked);

    let value;
    if (tableRowsChecked.length === 0)
        value = false;
    else if (tableRowsChecked.length < tableRows.length)
        value = "mixed";
    else
        value = true;

    setMenuPickerSelectAllChecked(target, value);
};

const menuPickerRowClick = (target, event) => {
    setMenuPickerChecked(target, !menuPickerLabel(target).firstChild.checked);
    menuPickerCheckPerformed(target);
};
