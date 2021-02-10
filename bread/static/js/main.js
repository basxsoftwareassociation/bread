
// support onload after page loaded for all elements
document.addEventListener(
    "DOMContentLoaded",
    (e) => { console.log('heeeeeeeeeee'); $$('[onload]:not(body):not(frame):not(iframe):not(img):not(input):not(link):not(script):not(style)')._.fire("load"); }
);


function initAllChoices(element=$("body")) {
    var selectElements = $$("select", element);
    for(let element of selectElements) {
        makeChoices(element);
    }
}

function makeChoices(selectElem) {
    // prevent initialization in template forms for django formsets
    if(selectElem.closest(".template-form")) {
        return null;
    }
    var choices = new Choices(selectElem, {
        /*
        classNames: {
            input: 'choices__input browser-default',
        }
        */
        searchResultLimit: 20
    });
    // TODO: wait for choices.js to fix the error when using space to separate classes
    // when fixed we can uncomment the code above and remove the line below
    // https://github.com/jshjohnson/Choices/issues/832
    $('input.choices__input', selectElem.parentNode.parentNode).classList.add("browser-default");

    // check readonly
    if(selectElem.hasAttribute("readonly")) {
        $(selectElem.parentNode)._.style({cursor: "not-allowed", pointerEvents: "none"});
        $(selectElem.parentNode.parentNode)._.style({cursor: "not-allowed", pointerEvents: "none"});
        $(selectElem.parentNode.parentNode.parentNode)._.style({cursor: "not-allowed"});
    }
    return choices;
}


function init_formset(form_prefix) {
    _update_add_button(form_prefix);
}

function delete_inline_element(checkbox, element) {
    checkbox.checked = true;
    element.style.display = "none";
}

function _update_add_button(form_prefix) {
    var formcount = $('#id_' + form_prefix + '-TOTAL_FORMS')
    var maxforms = $('#id_' + form_prefix + '-MAX_NUM_FORMS')
    var addbutton = $('#add_' + form_prefix + '_button')
    if(addbutton) {
        addbutton.style.display = "inline-flex";
        if(parseInt(formcount.value) >= parseInt(maxforms.value)) {
            addbutton.style.display = "none";
        }
    }
}

function formset_add(form_prefix, list_container) {
    var formcount = $('#id_' + form_prefix + '-TOTAL_FORMS')
    var newElementStr = $('#empty_' + form_prefix + '_form').innerHTML.replace(/__prefix__/g, formcount.value)
    var newElements = new DOMParser().parseFromString(newElementStr, "text/html").getElementsByTagName("body")[0].children;
    for(let element of newElements) {
        $(list_container).appendChild(element);
    }
    formcount.value = parseInt(formcount.value) + 1;
    _update_add_button(form_prefix);
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
    for(let checkbox of table.querySelectorAll('input[type=checkbox][data-event=select]')) {
        form.appendChild(checkbox.cloneNode(true));
    }
    document.body.appendChild(form);
    form.submit();
}
