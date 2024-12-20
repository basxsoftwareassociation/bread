// support onload after page loaded for all elements
document.addEventListener("DOMContentLoaded", () => basxbread_load_elements());

// same for ajax content
htmx.onLoad(function(content) {
        basxbread_load_elements();
});

function basxbread_load_elements() {
        $$(
                "[onload]:not(body):not(frame):not(iframe):not(img):not(link):not(script):not(style)"
        )._.fire("load");
        $$("select.autosort").forEach(breadSortSelect);
        $$("input.bread-ajax-search").forEach(initAjaxSearchField);

        setBasxBreadCookie("timezone", Intl.DateTimeFormat().resolvedOptions().timeZone);
}

// make sure to display content from faild ajax requests
htmx.on("htmx:responseError", function(event) {
        event.detail.target.innerHTML = event.detail.xhr.responseText;
});

// some helper which are used for the multiselect widget
function updateMultiselect(e) {
        let elem = $(".bx--list-box__selection", e);
        if (elem) {
                elem.firstChild.textContent = $$(
                        "fieldset input[type=checkbox][checked]",
                        e
                ).length;
        }
}

function filterOptions(e) {
        var searchterm = $("input.bx--text-input", e).value.toLowerCase();
        for (i of $$("fieldset .bx--list-box__menu-item", e)) {
                if (i.innerText.toLowerCase().includes(searchterm)) {
                        $(i)._.style({
                                display: "initial"
                        });
                } else {
                        $(i)._.style({
                                display: "none"
                        });
                }
        }
}

function clearMultiselect(e) {
        for (i of $$("fieldset input[type=checkbox][checked]", e)) {
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
        var formcount = $("#id_" + form_prefix + "-TOTAL_FORMS");
        var maxforms = $("#id_" + form_prefix + "-MAX_NUM_FORMS");
        var addbutton = $("#add_" + form_prefix + "_button");
        if (addbutton) {
                addbutton.style.display = "inline-flex";
                if (parseInt(formcount.value) >= parseInt(maxforms.value)) {
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
        var formcount = $("#id_" + form_prefix + "-TOTAL_FORMS");
        var newElementStr = $("#empty_" + form_prefix + "_form").innerText.replace(
                /__prefix__/g,
                formcount.value
        );
        placeholder.outerHTML = newElementStr;

        formcount.value = parseInt(formcount.value) + 1;
        update_add_button(form_prefix);
        updateMultiselect(container_elem);

        basxbread_load_elements();
        htmx.process(container_elem);
}

// Function which is used to collect checkboxes from a datatable and submit the selected checkboxes to a URL for bulk processing
function submitbulkaction(table, actionurl, method = "GET") {
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

        for (let checkbox of table.querySelectorAll(
                        "input[type=checkbox][data-event=select]"
                )) {
                form.appendChild(checkbox.cloneNode(true));
        }

        for (let checkbox of table.querySelectorAll(
                        "input[type=checkbox][data-event=select-all]"
                )) {
                form.appendChild(checkbox.cloneNode(true));
        }

        document.body.appendChild(form);
        form.submit();
}

// helper functions to set and get basxbread-namespaced cookies
function setBasxBreadCookie(key, value) {
        document.cookie =
                "basxbread-" + key + "=" + encodeURIComponent(value) + "; path=/";
}

function getBasxBreadCookie(key, _default = null) {
        var ret = document.cookie
                .split("; ")
                .find((row) => row.startsWith("basxbread-" + key + "="));
        if (!ret) return _default;
        ret = ret.split("=")[1];
        return ret ? decodeURIComponent(ret) : _default;
}

function getEditDistance(a, b) {
        if (a.length == 0) return b.length;
        if (b.length == 0) return a.length;

        var matrix = [];

        // increment along the first column of each row
        var i;
        for (i = 0; i <= b.length; i++) {
                matrix[i] = [i];
        }

        // increment each column in the first row
        var j;
        for (j = 0; j <= a.length; j++) {
                matrix[0][j] = j;
        }

        // Fill in the rest of the matrix
        for (i = 1; i <= b.length; i++) {
                for (j = 1; j <= a.length; j++) {
                        if (b.charAt(i - 1) == a.charAt(j - 1)) {
                                matrix[i][j] = matrix[i - 1][j - 1];
                        } else {
                                matrix[i][j] = Math.min(
                                        matrix[i - 1][j - 1] + 1, // substitution
                                        Math.min(
                                                matrix[i][j - 1] + 1, // insertion
                                                matrix[i - 1][j] + 1
                                        )
                                ); // deletion
                        }
                }
        }

        return matrix[b.length][a.length];
}

function searchMatchRank(searchTerms, value) {
        var score = 0;
        let valueTokens = value.toLowerCase().split(" ");
        for (let token of valueTokens) {
                var lowestScore = 999999;
                for (let term of searchTerms) {
                        if (token == term) {
                                lowestScore = 0;
                        } else if (token.startsWith(term)) {
                                lowestScore = 1 / term.length;
                        } else {
                                lowestScore = Math.min(getEditDistance(token, term), lowestScore);
                        }
                }
                score += lowestScore;
        }
        return score;
}

function breadSortSelect(selectNode) {
        optionNodes = Array.from(selectNode.children);
        comparator = new Intl.Collator().compare;
        optionNodes.sort((a, b) => comparator(a.textContent, b.textContent));
        optionNodes.forEach((option) => selectNode.appendChild(option));
}

function initAjaxSearchField(elem) {
        // close drop-down when user clicks anywhere else
        document.addEventListener('click', (ev) => {
                if (!elem.parentElement.parentElement.contains(ev.target))
                        elem.parentElement.nextElementSibling.nextElementSibling.style.display = 'none'
        });

        document.addEventListener('htmx:load', (ev) => {
                if (ev.detail.elt == document.body) {
                        return
                }
                if (ev.detail.elt.parentElement.parentElement.querySelector("input.bread-ajax-search") != elem) {
                        return;
                }
                $$('.result-item', ev.target)._.bind({
                        'click': (e) => {
                                elem.previousElementSibling.value = e.target.value;
                                elem.value = '';
                                elem.parentElement.nextElementSibling.firstElementChild.innerText = e.target.innerText;
                                elem.parentElement.nextElementSibling.style.display = 'flex';
                                elem.parentElement.nextElementSibling.nextElementSibling.innerHTML = '';
                                elem.parentElement.nextElementSibling.nextElementSibling.style.display = 'none';
                        }
                })
        })
}
