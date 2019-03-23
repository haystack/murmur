function sidebar_init() {
    var items = document.getElementsByTagName("main")[0].children;
    var target = ""

    for (i = 1; i < items.length; i++) {
        var current = items[i]

        if (current.tagName == 'DIV') {
            target = current.id + "sidebar";

            var sublist = document.createElement("li");

            var header_ref = document.createElement("a");
            header_ref.href = "#" + current.id;
            var text = current.children[0].innerHTML;
            var end = text.indexOf("<a");
            header_ref.innerHTML = text.substring(0, end);
            sublist.appendChild(header_ref);

            var actions = document.createElement("ul");
            actions.id = target;
            actions.className = "sidebar-list";
            sublist.appendChild(actions);

            document.getElementById("sidebar_container").appendChild(sublist);
        } else if (current.tagName == 'DIV' && !current.id.includes("-")) {
            // console.log(current);

            var action = document.createElement("li");

            var action_href = document.createElement("a");
            action_href.href = "#" + current.id;
            action_href.innerHTML = current.id;
            action.appendChild(action_href);

            document.getElementById(target).appendChild(action);

        }
    }
}
