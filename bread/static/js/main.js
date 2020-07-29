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

function initAllChoices() {
    var selectElements = $$("select.autocompleteselect, select.autocompleteselectmultiple");
    for(var i = 0; i < selectElements.length; ++i) {
        makeChoices(selectElements[i]);
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
    });
    // TODO: wait for choices.js to fix the error when using space to separate classes
    // when fixed we can uncomment the code above and remove the line below
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
    hide_item_on_delete_checkbox();
    // create an "Add" button if appropriate
    update_add_button(form_prefix);
}
function enable_materialize_newform(form) {
    var select_choices = $$("select.autocompleteselect", form);
    for(var i = 0; i < select_choices.length; ++i) {
        makeChoices(select_choices[i])
    }

    var m_input_fields = form.getElementsByClassName("input-field");
    for(var j = 0; j < m_input_fields.length; ++j) {
        var field = $("input", m_input_fields[j]);
        if(field)
            field.classList.remove('no-autoinit');
    }
    M.Datepicker.init(form.querySelectorAll('.datepicker'), {format: 'yyyy-mm-dd', showClearBtn: true, autoClose: true});
    M.AutoInit(form);

}

function hide_item_on_delete_checkbox() {
    $$("input[type=checkbox].delete")._.unbind("click");
    $$("input[type=checkbox].delete")._.bind({
        "click": function(e){
            $$("td:not(:last-child) > *", e.target.closest("tr")).map(function(elem){
                elem.classList.toggle("hide");
            });
        }
    });
}

function update_add_button(form_prefix) {
    var formcount = $('#id_' + form_prefix + '-TOTAL_FORMS')
    var maxforms = $('#id_' + form_prefix + '-MAX_NUM_FORMS')
    var addbutton = $('#add_' + form_prefix + '_button')
    addbutton.style.display = "inline-block";
    if(parseInt(formcount.value) >= parseInt(maxforms.value)) {
        addbutton.style.display = "none";
    }
}

function formset_add(form_prefix) {
    var formcount = $('#id_' + form_prefix + '-TOTAL_FORMS')
    console.log(form_prefix, formcount);
    var newElementStr = $('#empty_' + form_prefix + '_form').innerHTML.replace(/__prefix__/g, formcount.value)
    var newElem = new DOMParser().parseFromString(newElementStr, "text/html").getElementsByTagName('tr')[0];
    $('#formset_' + form_prefix + '_table tbody').appendChild(newElem);
    formcount.value = parseInt(formcount.value) + 1;
    enable_materialize_newform(newElem);
    update_add_button(form_prefix);
    hide_item_on_delete_checkbox(newElem);
}
