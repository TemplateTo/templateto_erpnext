frappe.ui.form.on("TemplateTo Settings", {
    test_connection: function (frm) {
        frappe.call({
            doc: frm.doc,
            method: "test_connection",
            freeze: true,
            freeze_message: __("Testing connection to TemplateTo API..."),
        });
    },
});
