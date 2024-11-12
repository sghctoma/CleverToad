import m, { redraw, request, mount } from "mithril";
import { parse, stringify } from 'smol-toml'

const ScrollableList = {
  oninit: (vnode) => {
    vnode.state.focusIndex = null;
    vnode.state.scrollAnchor = null;
  },

  // Utility functions defined within ScrollableList
  addItem: (vnode) => {
    const listName = vnode.attrs.title;
    App.config.prophecy_parts[listName].push("");
    vnode.state.focusIndex = App.config.prophecy_parts[listName].length - 1;

    // Scroll to the newly added item
    setTimeout(() => {
      if (vnode.state.scrollAnchor) {
        vnode.state.scrollAnchor.scrollIntoView({ behavior: "smooth", block: "end" });
      }
    }, 50);
  },

  updateItem: (vnode, index, value) => {
    const listName = vnode.attrs.title;
    App.config.prophecy_parts[listName][index] = value;
  },

  removeItem: (vnode, index) => {
    const listName = vnode.attrs.title;
    App.config.prophecy_parts[listName].splice(index, 1);
    vnode.state.focusIndex = null;
  },

  updateSearchQuery: (vnode, query) => {
    App.searchQueries[vnode.attrs.title] = query;
  },

  onEnterPress: (vnode, index) => {
    const listName = vnode.attrs.title;
    vnode.state.focusIndex = index + 1 < App.config.prophecy_parts[listName].length ? index + 1 : null;
  },

  view: (vnode) => {
    const listName = vnode.attrs.title;
    const name = (listName.charAt(0).toUpperCase() + listName.slice(1)).replace('_', ' ');
    const items = App.config.prophecy_parts[listName];
    const searchQuery = App.searchQueries[listName];

    return m(".list-container", [
      m(".list-title", name),
      m(".search-container", [
        m("input[type=text][placeholder=Search...]", {
          value: searchQuery,
          oninput: (e) => ScrollableList.updateSearchQuery(vnode, e.target.value)
        })
      ]),
      m(".list", [
        items
          .filter(item => item.toLowerCase().includes(searchQuery.toLowerCase()))
          .map((item, index) =>
            m(".item", [
              m("input[type=text]", {
                value: item,
                oncreate: (vnodeInput) => {
                  if (vnode.state.focusIndex === index) {
                    vnodeInput.dom.focus();
                  }
                },
                oninput: (e) => ScrollableList.updateItem(vnode, index, e.target.value),
                onkeypress: (e) => {
                  if (e.key === "Enter") {
                    ScrollableList.onEnterPress(vnode, index);
                  }
                }
              }),
              m("button", { onclick: () => ScrollableList.removeItem(vnode, index) }, "X")
            ])
          ),
        m("div.scroll-anchor", {
          oncreate: (vnodeAnchor) => { vnode.state.scrollAnchor = vnodeAnchor.dom; }
        })
      ]),
      m(".add-item", m("button", { onclick: () => ScrollableList.addItem(vnode) }, `Add ${listName.replace('_', ' ').slice(0, -1)}`))
    ]);
  }
};

const App = {
  config: {},
  scrollAnchors: {
    "subjects": null,
    "actions": null,
    "objects": null,
    "spatial_prepositions": null,
    "temporal_prepositions": null,
    "places": null,
    "times": null
  },
  focusIndex: {
    "subjects": null,
    "actions": null,
    "objects": null,
    "spatial_prepositions": null,
    "temporal_prepositions": null,
    "places": null,
    "times": null
  },
  searchQueries: {
    "subjects": "",
    "actions": "",
    "objects": "",
    "spatial_prepositions": "",
    "temporal_prepositions": "",
    "places": "",
    "times": ""
  },
  statusMessage: "",
  statusColor: "",

  async oninit() {
    App.config = await App.fetchConfig();
  },

  setStatus: (message, color) => {
    App.statusMessage = message;
    App.statusColor = color;
    redraw();

    // Clear the message after 5 seconds
    setTimeout(() => {
      if (App.statusMessage === message) {
        App.statusMessage = "";
        redraw();
      }
    }, 2000);
  },

  speak: (message) => {
    request({
      method: "GET",
      url: `/speak?${message}`
    })
  },

  // Fetch config from server
  fetchConfig: async () => {
    try {
      const response = await request({ method: "GET", url: `/config` });
      return response;
    } catch (error) {
      console.error("Failed to fetch lists data:", error);
      return {
        "dice_type": 20,
        "critical_fail": "You borfed it.",
        "critical_success": "High Roller, indeed!",
        "prophecy_parts": {
          "subjects": [],
          "actions": [],
          "objects": [],
          "spatial_prepositions": [],
          "temporal_prepositions": [],
          "places": [],
          "times": []
        }
      };
    }
  },

  // Save config to the server
  saveConfig: (data) => {
    request({
      method: "PUT",
      url: "/config",
      body: data,
      headers: { "Content-Type": "application/json" }
    }).then(
      () => App.setStatus("Config saved successfully!", "#228B22"),
      () => App.setStatus("Error saving config. Please try again.", "#b22222")
    );
  },

  // Import lists from a TOML file
  importConfig: (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const parsedData = parse(e.target.result);
          App.config = parsedData;
          m.redraw(); // Refresh the Mithril view
          App.setStatus("Config imported successfully!", "#228B22");
        } catch (error) {
          console.error("Failed to parse TOML file:", error);
          App.setStatus("Invalid config file!", "#b22222");
        }
      };
      reader.readAsText(file);
    }
  },

  // Export lists to a TOML file
  exportConfig: () => {
    const tomlData = stringify(App.config);
    const blob = new Blob([tomlData], { type: "text/plain" });
    const url = URL.createObjectURL(blob);

    // Create a temporary link and trigger download
    const a = document.createElement("a");
    a.href = url;
    a.download = "config.toml";
    a.click();
    URL.revokeObjectURL(url); // Clean up the URL after download
  },

  // view
  view: () => m(".container", [
    m("h1", "Clever Toad Config"),
    m(".scrollable-container", [
      m("h2", "Dice rolling"),
      m(".dice-preference-container", [
        m("label", "Sides:"),
        m("input[type=number][min=2]", {
          value: App.config.dice_type,
          oninput: (e) => App.config.dice_type = parseInt(e.target.value)
        }),
        m("button.play", { style: "border-color: transparent; cursor: default" })
      ]),
      m(".dice-preference-container", [
        m("label", "Natural  1:"),
        m("input[type=text]", {
          value: App.config.critical_fail,
          oninput: (e) => App.config.critical_fail = e.target.value
        }),
        m("button.play", { onclick: () => App.speak(App.config.critical_fail) })
      ]),
      m(".dice-preference-container", [
        m("label", `Natural ${App.config.dice_type}`),
        m("input[type=text]", {
          value: App.config.critical_success,
          oninput: (e) => App.config.critical_success = e.target.value
        }),
        m("button.play", { onclick: () => App.speak(App.config.critical_success) })
      ]),
      m("h2", "Prophecies"),
      m(".prophecies-container", [
        ["subjects", "actions", "objects"].map(listName =>
          m(ScrollableList, { title: listName })
        )
      ]),
      m(".prophecies-container", [
        ["spatial_prepositions", "places"].map(listName =>
          m(ScrollableList, { title: listName })
        )
      ]),
      m(".prophecies-container", [
        ["temporal_prepositions", "times"].map(listName =>
          m(ScrollableList, { title: listName })
        )
      ])
    ]),

    App.statusMessage ? m(".status-bar", { style: { color: App.statusColor } }, App.statusMessage) : null,

    m(".config-button-container", [
      m("button", { onclick: () => App.saveConfig(App.config) }, "Save"),
      m("input[type=file][id=import-config]", { onchange: App.importConfig, accept: ".toml" }),
      m("label.import-button", { for: "import-config" }, "Import"),
      m("button", { onclick: () => App.exportConfig() }, "Export")
    ]),
  ])
};

// Mount the app
mount(document.getElementById("app"), App);
