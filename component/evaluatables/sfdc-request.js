javascript@runtime:(function () {
    var data = context.getData();
    var eventData = JSON.parse(
        context.getGlobalServices().getJsonService().toJsonString(data)
    );

    // Unwrap Extole's { value: "..." } field wrappers
    function unwrap(obj) {
        var out = {};
        for (var k in obj) {
            if (obj.hasOwnProperty(k)) {
                out[k] = (obj[k] && obj[k].value != null) ? obj[k].value : obj[k];
            }
        }
        return out;
    }

    var d = unwrap(eventData);

    if (!d.email) return null;

    // Top-level identity fields — everything else goes into data{}
    var topLevel = { event_id: 1, event_name: 1, email: 1, salesforce_id: 1 };
    var extra = {};
    for (var k in d) {
        if (d.hasOwnProperty(k) && !topLevel[k]) {
            extra[k] = d[k];
        }
    }

    var body = {
        event_id:      d.event_id      || null,
        event_name:    d.event_name    || null,
        email:         d.email,
        salesforce_id: d.salesforce_id || null,
        data:          extra
    };

    // Authorization header is added automatically by the OAUTH_SFDC algorithm
    return context.createRequestBuilder()
        .withMethod('POST')
        .addHeader('Content-Type', 'application/json')
        .withBody(JSON.stringify(body))
        .build();
})();
