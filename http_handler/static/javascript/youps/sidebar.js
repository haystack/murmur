function sidebar_init() {
    /* USAGE
     *   - Divs to be added to the sidebar need the class `add-sidebar`
     *   - Another class specifies the level [`header`, `sub-header`, `value`]
     *      - Each level will fall into the list of the last higher level
     *      - `header` and `sub-header` use the innerHTML
     *      - `value` uses the id of the div
     */

    var items = document.getElementsByClassName("add-sidebar")
    var header = ""
    var target = ""

    for (i = 0; i < items.length; i++) {
        var current = items[i]

        if (current.classList.contains("header")) {

            header = current.id + "sidebar";

            let sublist = document.createElement("li");
            let header_ref = document.createElement("a");
            header_ref.href = "#" + current.id;

            let text = current.children[0].innerHTML;
            let end = text.indexOf("<a");
            header_ref.innerHTML = text.substring(0, end);
            sublist.appendChild(header_ref);

            let actions = document.createElement("ul");
            actions.id = header;
            actions.className = "sidebar-list";
            sublist.appendChild(actions);

            document.getElementById("sidebar_container").appendChild(sublist);
        }

        if (current.classList.contains("sub-header")) {

            target = current.id + "sidebar";

            let sublist = document.createElement("li");
            let header_ref = document.createElement("a");
            header_ref.href = "#" + current.id;

            let text = current.children[0].innerHTML;
            let end = text.indexOf("<a");
            header_ref.innerHTML = text.substring(0, end);
            sublist.appendChild(header_ref);

            let actions = document.createElement("ul");
            actions.id = target;
            actions.className = "sidebar-list";
            sublist.appendChild(actions);

            document.getElementById(header).appendChild(sublist);
        }


        if (current.classList.contains("value")) {
            let action = document.createElement("li");

            let action_href = document.createElement("a");
            action_href.href = "#" + current.id;
            action_href.innerHTML = current.id;
            action.appendChild(action_href);

            document.getElementById(target).appendChild(action);
        }
    }
}
