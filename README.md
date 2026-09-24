# extole-sfdc-component

The Extole-side integration component bundle for Salesforce CRM. This is what shows up as the
"Salesforce" listing in Extole's partner integration catalog (`my.extole.com/partners/...`), and
it's the counterpart to [`extole-sfdc-app`](https://github.com/extole/extole-sfdc-app) (the
Salesforce-side managed package): this repo defines what Extole sends/receives and how it's
presented in Extole's own UI; `extole-sfdc-app` defines what Salesforce does with it.

There is currently **no deploy script** — installing this bundle means walking the tree below and
creating each piece via the Extole Management API by hand. See [Manual install](#manual-install).

## What's in this repo

```
component/
  component.json                                    # campaign wrapper ("Extole for Salesforce")
  components/
    salesforce/
      component.json                                # the integration listing itself
      components/
        sfdc_person_card/
          component.json                             # person-card data zone (nested under salesforce)
      evaluatables/
        sfdc-request.js                               # outbound webhook request builder
        sfdc-card-render.js                            # person-card response builder
    salesforce_raf/
      component.json                                 # advocate SHAREABLE-event writeback companion
salesforce_integration_v10.0_reference.json           # build notes, not a deployable component
```

### `component/component.json` — root
A `campaign_type: INTEGRATION` campaign named "Extole for Salesforce" that everything else lives
under. Its `tags` still say `internal:integration-component-name:salesforce` — see
[Naming collision](#naming-collision-must-fix-before-installing) before deploying this as-is.

### `component/components/salesforce/component.json` — the integration itself
An `integration-v10.0` component. Two settings an installer fills in:

- **`sfdcEndpointUrl`** — the Salesforce org's inbound webhook URL, copied from `extole-sfdc-app`'s
  Receive Extole Events tab (`https://<org>.my.salesforce.com/services/apexrest/extole/events`).
- **`clientKey`** (type `CLIENT_KEY`) — the Extole Security Center key backing the Salesforce
  Connected App's OAuth Client Credentials flow. Set up per `extole-sfdc-app`'s INSTALL.md Step 10.

It also declares one webhook element (`elements.webhooks[0]`) — this is the actual outbound POST
to Salesforce, built from `sfdc-request.js`, authenticated via `clientKey`, tagged
`internal:app_type=extole-sfdc-app` so sibling components (see `salesforce_raf` below) can find it
by tag instead of by a hardcoded id. **`sfdc-request.js` must use
`context.createRequestBuilderWithDefaults()`, not `context.createRequestBuilder()`** — only the
`WithDefaults()` variant attaches the `clientKey`'s Authorization header (see
[PR #1](https://github.com/extole/extole-sfdc-component/pull/1), already fixed).

A hidden `eventsWebhook` setting resolves that same webhook's id at build time by querying for
`WEBHOOK` elements tagged `internal:app_type=extole-sfdc-app` — useful for referencing it from
other settings without needing to know its id ahead of time.

The `views` `MULTI_SOCKET` (filtered to `config-view-v10.0` / `event-stream-view-v10.0`) is where
the config UI lives — a `configuration` config-view child (declared separately, socketed in at
install time) displays `sfdcEndpointUrl` + `clientKey` as the two fields an admin fills in, with a
build-time `status` of `READY`/`IN_PROGRESS` depending on whether `sfdcEndpointUrl` has been
changed from its placeholder value.

Per `salesforce_integration_v10.0_reference.json`'s build notes: **the `businessEvents`
`MULTI_SOCKET` is not in the initial component definition — it has to be added in a follow-up
`POST /v1/components/{id}/settings` call after the component is created**, then the actual
business events (Lead Created, Opportunity Created, Opportunity Closed Won, etc.) get socketed
into it. Those events live in the **same `campaign_id`** as the integration component, not in a
separate campaign — in practice, for a specific client install, they typically live directly in
that client's own referral campaign (see `extole-sfdc-app`'s INSTALL.md Step 10), not duplicated
here.

### `sfdc_person_card` — nested under `salesforce`
A `content-v10.0` component with a `FRONTEND_CONTROLLER` step that responds to an `sfdc_person_card`
input event, rendering via `sfdc-card-render.js`. This is what `extole-sfdc-app`'s Person Card LWC
(on the Lead/Contact record page) calls to get that person's share links, referred friends, and
reward state.

### `salesforce_raf` — sibling of `salesforce`
Fires on advocate `SHAREABLE` events in the `ADVOCATE` journey and dispatches to the *same* webhook
as `salesforce` — it finds it at build time by walking its parent's children and querying for a
`WEBHOOK` tagged `internal:app_type=extole-sfdc-app`, the same tag `salesforce`'s own webhook
carries. This means `salesforce_raf` must be socketed as a **sibling** of `salesforce` (same parent),
not a child of it, for that lookup to find anything.

## Naming collision — must fix before installing

Every `component.json` here still uses the bare name `salesforce` (see each file's `tags`:
`internal:integration-component-name:salesforce`). That collides with Extole's own official
partner catalog listing, which is also named `salesforce` but is actually **Salesforce Commerce
Cloud**, not CRM — installing this bundle verbatim makes `my.extole.com/partners/salesforce` render
the wrong (Commerce Cloud) partner page for your client. Rename every occurrence of
`internal:integration-component-name:salesforce` to something unambiguous (e.g. `salesforce_crm`)
before deploying, and give the components themselves non-colliding `name` values to match.

## Manual install

There's no deploy script yet, so this is done by hand via the Extole Management API (or the Extole
MCP/CLI tooling, if available), roughly in this order:

1. **Create the campaign** from `component/component.json`'s `elements.campaign` block — apply the
   naming fix above first.
2. **Create the root component**, then the `salesforce` integration component underneath it from
   `component/components/salesforce/component.json`, including its settings and its `elements.webhooks[0]`.
3. **Add the `businessEvents` `MULTI_SOCKET`** to the `salesforce` component via a follow-up
   `POST /v1/components/{id}/settings` call (per the build notes — it isn't part of the initial
   definition).
4. **Socket in `sfdc_person_card`** as a child of `salesforce`.
5. **Socket in `salesforce_raf`** as a sibling of `salesforce` (same parent as `salesforce`, not a
   child of it — see above).
6. **Socket in a `config-view-v10.0` child** (a `configuration` view) under `salesforce`'s `views`
   socket, displaying `sfdcEndpointUrl` and `clientKey`.
7. In the client's actual referral campaign, add the business events (Lead Created, Opportunity
   Created, Opportunity Closed Won, Signed Up, etc.) that should trigger writeback, each with a
   `WEBHOOK` action pointed at the `salesforce` component's webhook — see `extole-sfdc-app`'s
   INSTALL.md Step 10 for the Salesforce-side half of this (Connected App, `CLIENT_KEY`, endpoint
   URL).

**Known gap:** the currently-live reference build (client `salesforce-crm-sandbox`, campaign
`7688489761726638552`, component `7688490161567149942`) predates the `eventsWebhook` setting, the
`views` socket's type filter, `sfdc_person_card`, and `salesforce_raf` — it only has the bare
`salesforce` component and its `configuration` view child. It was built manually against an earlier
version of this repo's `component.json` files and hasn't been resynced. Worth rebuilding fresh
against the current source rather than trying to patch it incrementally, next time someone installs
this for real.
