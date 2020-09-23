function tableToExcel(downloadelement, tableelement, worksheetname, filename) {
    // e.g. <input type="button" onclick="tableToExcel(this, tableelement, 'mysheet', 'myfile.xls')" value="Export to Excel">
    var uri = 'data:application/vnd.ms-excel;base64,'
    var template = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40"><meta charset="utf-8"/><head><!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet><x:Name>{worksheet}</x:Name><x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions></x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]--></head><body><table>{table}</table></body></html>'
    var base64 = function (s) { return window.btoa(unescape(encodeURIComponent(s))) }
    var format = function (s, c) { return s.replace(/{(\w+)}/g, function (m, p) { return c[p]; }) }
    var ctx = { worksheet: worksheetname || 'Worksheet', table: table.innerHTML }

    downloadelement.href = uri + base64(format(template, ctx));
    downloadelement.download = filename;
    downloadelement.click();
}

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

// REFACTORING:

function init_formset(form_prefix) {
    // prevent materialize init in template form
    var m_input_fields  = $$('#empty_' + form_prefix + '_form .input-field')
    for(var j = 0; j < m_input_fields.length; ++j) {
        var field = $("input, select", m_input_fields[j]);
        if(field)
            field.classList.add('no-autoinit');
    }
    _update_add_button(form_prefix);
}
function _init_materialize(element) {
    var m_input_fields = element.getElementsByClassName("input-field");
    for(var j = 0; j < m_input_fields.length; ++j) {
        var field = $("input", m_input_fields[j]);
        if(field)
            field.classList.remove('no-autoinit');
    }
    M.Datepicker.init(element.querySelectorAll('.datepicker'), {format: 'yyyy-mm-dd', showClearBtn: true, autoClose: true});
    M.AutoInit(element);
}

function delete_inline_element(checkbox, inlinecontainer, deletelabel) {
    checkbox.checked = !checkbox.checked;
    inlinecontainer.style.height = checkbox.checked ? "3rem" : "initial";
    inlinecontainer.style.overflow = checkbox.checked ? "hidden" : "initial";
    inlinecontainer.style.backgroundColor = checkbox.checked ? "#999" : "initial";
    deletelabel.firstElementChild.innerText = checkbox.checked ? "undo" : "delete";
    deletelabel.parentElement.previousElementSibling.style.display = checkbox.checked ? "block" : "none";
}

function _update_add_button(form_prefix) {
    var formcount = $('#id_' + form_prefix + '-TOTAL_FORMS')
    var maxforms = $('#id_' + form_prefix + '-MAX_NUM_FORMS')
    var addbutton = $('#add_' + form_prefix + '_button')
    addbutton.style.display = "inline-block";
    if(parseInt(formcount.value) >= parseInt(maxforms.value)) {
        addbutton.style.display = "none";
    }
}

function formset_add(form_prefix, list_container) {
    var formcount = $('#id_' + form_prefix + '-TOTAL_FORMS')
    var newElementStr = $('#empty_' + form_prefix + '_form').innerHTML.replace(/__prefix__/g, formcount.value)
    var newElements = new DOMParser().parseFromString(newElementStr, "text/html").getElementsByTagName("body")[0].children;
    for(let element of newElements) {
        $(list_container).appendChild(element);
        initAllChoices(element);
        _init_materialize(element);
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
            M.toast({html: "Field " + label.innerText + " is not valid"})
            error = true;
        }
    }
    if(error)
        M.toast({html: "There are errors in some fields"})
}
