
// support onload after page loaded for all elements
document.addEventListener(
    "DOMContentLoaded",
    () => bread_load_elements()
);

htmx.onLoad(function(content) { bread_load_elements(); })

function bread_load_elements() {
    $$('[onload]:not(body):not(frame):not(iframe):not(img):not(link):not(script):not(style)')._.fire("load")
}

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

function makeChoices(selectElem) {
    // prevent initialization in template forms for django formsets
    if(selectElem.closest(".template-form")) {
        return null;
    }
    var choices = new Choices(selectElem, {
        removeItemButton: true,
        position: 'bottom',
        itemSelectText: '',
        classNames: {
            containerOuter: 'choices',
            containerInner: 'choices__inner',
            input: 'choices__input',
            inputCloned: 'choices__input--cloned bx--text-input',
            list: 'choices__list',
            listItems: 'choices__list--multiple',
            listSingle: 'choices__list--single',
            listDropdown: 'choices__list--dropdown',
            item: 'choices__item bx--tag',
            itemSelectable: 'choices__item--selectable',
            itemDisabled: 'choices__item--disabled',
            itemChoice: 'choices__item--choice',
            placeholder: 'choices__placeholder',
            group: 'choices__group',
            groupHeading: 'choices__heading',
            button: 'choices__button',
            activeState: 'is-active',
            focusState: 'is-focused',
            openState: 'is-open',
            disabledState: 'is-disabled',
            highlightedState: 'is-highlighted',
            selectedState: 'is-selected',
            flippedState: 'is-flipped',
            loadingState: 'is-loading',
            noResults: 'has-no-results',
            noChoices: 'has-no-choices'
        },
    });
    // check readonly
    if(selectElem.hasAttribute("readonly")) {
        $(selectElem.parentNode)._.style({cursor: "not-allowed", pointerEvents: "none"});
        $(selectElem.parentNode.parentNode)._.style({cursor: "not-allowed", pointerEvents: "none"});
        $(selectElem.parentNode.parentNode.parentNode)._.style({cursor: "not-allowed"});
    }
    return choices;
}


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

function validate_fields() {
    var error = false;
    for(input of $$("input")) {
        if(!input.checkValidity()) {
            var label = $("label[for=" + input.id + "]");
            if(!label)
                label = input;
            console.log("Field " + label.innerText + " is not valid")
            error = true;
        }
    }
    if(error)
        console.log("There are errors in some fields")
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

// added a temporary bug fix for expandable tiles before getting carbon library updated.
window.setExpandableTileMaxHeight = target => {
    // note: atf = above the fold,
    // btf = below the fold
    const atf = target.querySelector("[data-tile-atf]");
    const btf = target.querySelector(".bx--tile-content__below-the-fold");
    const atfHeight = atf.getBoundingClientRect().height;
    const btfHeight = btf.getBoundingClientRect().height;
    if (target.classList.contains("bx--tile--is-expanded"))
        target.style.maxHeight = `${atfHeight + btfHeight}px`;
    else
        target.style.maxHeight = `${atfHeight}px`;
};
const expandableTileObserver = new MutationObserver(mutations => {
    for (let mutation of mutations) {
        if (mutation.attributeName === "class") {
            window.setExpandableTileMaxHeight(mutation.target);
        }
    }
});
const expandableTileDOMObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
        window.setExpandableTileMaxHeight(entry.target);
    });
}, {
    root: null,
    rootMargin: "0px",
    threshold: 0.1,
})
document.addEventListener("load", function() {
    const expandableTiles = document.querySelectorAll(".bx--tile.bx--tile--expandable");
    for (let tile of expandableTiles) {
        expandableTileObserver.observe(tile, { attributes: true, });
        expandableTileDOMObserver.observe(tile);
    }
});
document.addEventListener("unload", function() {
    expandableTileDOMObserver.disconnect();
});

// js code for menu picker
function menuPickerLabel(trElement) {
    return trElement.firstChild.firstChild.firstChild;
}
function menuPickerUncheck(trElement) {
    const label = menuPickerLabel(trElement);
    label.setAttribute("data-contained-checkbox-state", "false")
    label.firstChild.checked = false;
    label.firstChild.setAttribute("aria-checked", "false")
}
const menuPickerAdd = target => {
    const menuPickerId = target.getAttribute("data-menuid");
    const datatable = target.closest(".bread--menupicker");
    const selectedRowsTable = datatable.querySelector(".bread--menupicker__selected-table tbody")
    const unselectedRows = [...datatable.querySelectorAll(".bread--menupicker__unselected-table tbody tr")];

    // browse all checked rows
    const checkedUnselected = unselectedRows.filter(
        el => menuPickerLabel(el).getAttribute("data-contained-checkbox-state") === "true"
    );

    // move the checked rows to the left, in the preserved order.
    if (checkedUnselected.length > 0) {
        selectedRowsTable.append(...checkedUnselected);
        checkedUnselected.forEach(el => {
            const checkbox = menuPickerLabel(el).firstChild;
            const inputTag = document.createElement("input");
            inputTag.setAttribute("type", "hidden");
            inputTag.setAttribute("name", checkbox.name);
            inputTag.setAttribute("value", checkbox.value);
            datatable.appendChild(inputTag);
        });
        [...selectedRowsTable.children]
            .sort((a, b) =>
                parseInt(a.firstChild.getAttribute("data-order"))
                - parseInt(b.firstChild.getAttribute("data-order"))
            )
            .forEach(el => {
                menuPickerUncheck(el);
                selectedRowsTable.appendChild(el);
            });
    }
};
const menuPickerRemove = target => {
    const menuPickerId = target.getAttribute("data-menuid");
    const datatable = target.closest(".bread--menupicker");
    const unselectedRowsTable = datatable.querySelector(".bread--menupicker__unselected-table tbody");
    const selectedRows = [...datatable.querySelectorAll(".bread--menupicker__selected-table tbody tr")];

    // browse all checked rows
    const checkedSelected = selectedRows.filter(
        el => menuPickerLabel(el).getAttribute("data-contained-checkbox-state") === "true"
    );

    // move the checked rows to the right, in the preserved order.
    if (checkedSelected.length > 0) {
        unselectedRowsTable.append(...checkedSelected);
        checkedSelected.forEach(el => {
            const checkbox = menuPickerLabel(el).firstChild;
            const inputHidden = datatable.querySelector(`input[type="hidden"][name="${checkbox.getAttribute('name')}"][value="${checkbox.getAttribute('value')}"]`);
            datatable.removeChild(inputHidden);
        });
        [...unselectedRowsTable.children]
            .sort((a, b) =>
                parseInt(a.firstChild.getAttribute("data-order"))
                - parseInt(b.firstChild.getAttribute("data-order"))
            )
            .forEach(el => {
                menuPickerUncheck(el);
                unselectedRowsTable.appendChild(el);
            });
    }
};
const menuPickerLoad = menuPicker => {
    menuPicker.closest("form").addEventListener("submit", e => {
        e.preventDefault();

        alert('sent');
        const selectedRows = [...e.target.querySelectorAll(".bread--menupicker__selected-table tbody tr")];
        const unselectedRows = [...e.target.querySelectorAll(".bread--menupicker__unselected-table tbody tr")];

        selectedRows.forEach(el => {
            menuPickerUncheck(el);
        });
        unselectedRows.forEach(el => menuPickerUncheck(el));

        e.submit();
    });
};