javascript@runtime:(function () {
    var person    = context.getPerson();
    var stepEvent = context.getStepEvent();

    if (!person || !person.email) return null;

    var primaryStep  = context.getPrimaryStep();
    var salesforceId = person.data ? (person.data['salesforce_id'] || null) : null;

    var extra = {};
    if (stepEvent) {
        var stepData = JSON.parse(
            context.getGlobalServices().getJsonService().toJsonString(stepEvent.getData())
        );
        for (var k in stepData) {
            if (stepData.hasOwnProperty(k)) extra[k] = stepData[k];
        }
    }

    // extole-sfdc-app's inbound endpoint reads event_name and event_id from the top level
    // and the rest from `data` (data.email, data.salesforce_id, data.first_name,
    // data.last_name), so the person fields go inside `data`.
    extra.email = person.email;
    if (salesforceId) extra.salesforce_id = salesforceId;
    if (person.firstName) extra.first_name = person.firstName;
    if (person.lastName) extra.last_name = person.lastName;

    var body = {
        event_id:   primaryStep ? primaryStep.getId() : null,
        event_name: context.getStepName ? context.getStepName() : null,
        data:       extra
    };

    // createRequestBuilderWithDefaults() is required here -- only it attaches
    // the CLIENT_KEY setting's Authorization header (via the OAUTH_SFDC
    // algorithm). createRequestBuilder() alone silently omits it, producing
    // a request that looks correct in every other way (right URL, right
    // body) but is unauthenticated and gets a 401 INVALID_SESSION_ID.
    return context.createRequestBuilderWithDefaults()
        .withMethod('POST')
        .addHeader('Content-Type', 'application/json')
        .withBody(JSON.stringify(body))
        .build();
})();
