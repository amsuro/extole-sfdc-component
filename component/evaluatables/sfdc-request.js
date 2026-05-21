javascript@runtime:(function () {
    // Try to get identity from step context APIs first (action-v10.0 route),
    // fall back to getData() for legacy controller route.
    var email = null, eventName = null, eventId = null, salesforceId = null, extra = {};

    var step   = context.getStep   ? context.getStep()   : null;
    var person = context.getPerson ? context.getPerson() : null;

    if (person && step) {
        email        = person.getEmail();
        eventName    = step.getName();
        eventId      = step.getId();
        salesforceId = person.getData('salesforce_id') || null;

        // Include all custom step data as extra fields
        var stepData = JSON.parse(
            context.getGlobalServices().getJsonService().toJsonString(step.getData())
        );
        for (var k in stepData) {
            if (stepData.hasOwnProperty(k)) extra[k] = stepData[k];
        }
    } else {
        // Legacy: data came from controller action's explicit data block
        var raw = JSON.parse(
            context.getGlobalServices().getJsonService().toJsonString(context.getData())
        );

        function unwrap(obj) {
            var out = {};
            for (var k in obj) {
                if (obj.hasOwnProperty(k)) {
                    out[k] = (obj[k] && obj[k].value != null) ? obj[k].value : obj[k];
                }
            }
            return out;
        }

        var d     = unwrap(raw);
        email        = d.email;
        eventName    = d.event_name;
        eventId      = d.event_id;
        salesforceId = d.salesforce_id || null;

        var topLevel = { event_id: 1, event_name: 1, email: 1, salesforce_id: 1 };
        for (var k in d) {
            if (d.hasOwnProperty(k) && !topLevel[k]) extra[k] = d[k];
        }
    }

    if (!email) return null;

    var body = {
        event_id:      eventId      || null,
        event_name:    eventName    || null,
        email:         email,
        salesforce_id: salesforceId || null,
        data:          extra
    };

    // Authorization header is added automatically by the OAUTH_SFDC algorithm
    return context.createRequestBuilder()
        .withMethod('POST')
        .addHeader('Content-Type', 'application/json')
        .withBody(JSON.stringify(body))
        .build();
})();
