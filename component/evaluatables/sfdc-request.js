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

    var body = {
        event_id:      primaryStep  ? primaryStep.getId()    : null,
        event_name:    context.getStepName ? context.getStepName() : null,
        email:         person.email,
        salesforce_id: salesforceId,
        data:          extra
    };

    // Authorization header is added automatically by the OAUTH_SFDC algorithm
    return context.createRequestBuilder()
        .withMethod('POST')
        .addHeader('Content-Type', 'application/json')
        .withBody(JSON.stringify(body))
        .build();
})();
