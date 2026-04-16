"""
Extole Component API client.
Handles all HTTP interactions with /v1/components.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL  = os.getenv("EXTOLE_API_BASE", "https://api.extole.io")
API_TOKEN = os.getenv("EXTOLE_API_TOKEN", "")


def _headers():
    return {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }


def _raise(res):
    if not res.ok:
        raise RuntimeError(f"HTTP {res.status_code}: {res.text}")


# ── Campaign ───────────────────────────────────────────────────────────────────

def create_campaign(name, description=""):
    """Create a new campaign to house the Salesforce integration component."""
    res = requests.post(
        f"{BASE_URL}/v2/campaigns",
        headers=_headers(),
        json={"name": name, "description": description},
    )
    _raise(res)
    return res.json()


def delete_campaign(campaign_id):
    """Delete a campaign."""
    res = requests.delete(f"{BASE_URL}/v2/campaigns/{campaign_id}", headers=_headers())
    _raise(res)


# ── Integration discovery ──────────────────────────────────────────────────────

def find_salesforce_integration():
    """Return the component dict for the 'salesforce' integration-v10.0, or None."""
    res = requests.get(
        f"{BASE_URL}/v1/components",
        headers=_headers(),
        params={"having_any_types": "integration-v10.0"},
    )
    _raise(res)
    for c in res.json():
        if c.get("name") == "salesforce":
            return c
    return None


# ── Integration creation ───────────────────────────────────────────────────────

def create_salesforce_integration(campaign_id):
    """
    Create the Salesforce integration-v10.0 component in the given campaign,
    then add the businessEvents MULTI_SOCKET to it.
    Returns the component dict.
    """
    payload = {
        "name":        "salesforce",
        "types":       ["integration-v10.0"],
        "campaign_id": campaign_id,
        "settings": [
            {"name": "short.description",        "values": {"default": "Send Salesforce CRM events into Extole FlowBuilder"}},
            {"name": "about",                    "values": {"default": "Trigger referral and loyalty flows from Salesforce Opportunity, Lead, Contact, and Account events."}},
            {"name": "documentation.url",        "values": {"default": "https://dev.extole.com/docs/salesforce-integration"}},
            {"name": "external.url",             "values": {"default": "https://salesforce.com"}},
            {"name": "external.integration.url", "values": {"default": "https://salesforce.com/setup/integrations"}},
            {"name": "categories",               "values": {"default": "CRM"}},
            {"name": "logo",                     "values": {"default": "https://www.extole.com/wp-content/uploads/2023/07/Extole-icon-bug.svg"}},
            {"name": "imageKey",                 "values": {"default": "salesforce"}},
        ],
    }
    res = requests.post(f"{BASE_URL}/v1/components", headers=_headers(), json=payload)
    _raise(res)
    component = res.json()

    # Add the businessEvents MULTI_SOCKET — not part of the type schema, must be added explicitly
    socket_res = requests.post(
        f"{BASE_URL}/v1/components/{component['id']}/settings",
        headers=_headers(),
        json={
            "name":    "businessEvents",
            "type":    "MULTI_SOCKET",
            "filters": [{"component_type": "business-event-v10.0", "type": "COMPONENT_TYPE"}],
        },
    )
    _raise(socket_res)

    return component


# ── Business event socket ──────────────────────────────────────────────────────

def list_business_events(integration_id):
    """Return list of installed business-event components on the integration."""
    res = requests.get(
        f"{BASE_URL}/v1/components/{integration_id}/settings/businessEvents/installed-components",
        headers=_headers(),
    )
    _raise(res)
    return res.json()


def find_business_event(integration_id, event_name):
    """Return the installed business-event component matching event_name, or None."""
    for c in list_business_events(integration_id):
        if c.get("name") == event_name:
            return c
    return None


# ── Business event lifecycle ───────────────────────────────────────────────────

def _derive_display_names(event_name):
    """opportunity_won -> ('Opportunity Won', 'Opportunities Won', 'Opportunity Win Rate')"""
    words = event_name.replace("_", " ").title()
    return words, words + "s", words.rsplit(" ", 1)[0] + " Rate"


def create_business_event(event_name, campaign_id):
    """
    Create a business-event-v10.0 component in the given campaign.
    journeyName is intentionally omitted — that's a campaign-level concern.
    Returns the component dict.
    """
    singular, plural, rate = _derive_display_names(event_name)
    payload = {
        "name":        event_name,
        "types":       ["business-event-v10.0"],
        "campaign_id": campaign_id,
        "settings": [
            {"name": "singularNounName",  "values": {"default": singular}},
            {"name": "pluralNounName",    "values": {"default": plural}},
            {"name": "rateName",          "values": {"default": rate}},
            {"name": "dataCapturePolicy", "values": {"default": "ALL_DATA"}},
            {"name": "dataCopyScope",     "values": {"default": "PRIVATE"}},
            {"name": "adminUIIcon",       "values": {"default": "far fa-cloud"}},
            {"name": "adminUIColor",      "values": {"default": "#00A1E0"}},
            {"name": "aliases",           "values": {"default": ""}},
            {"name": "sequence",          "values": {"default": "1"}},
        ],
    }
    res = requests.post(f"{BASE_URL}/v1/components", headers=_headers(), json=payload)
    _raise(res)
    return res.json()


def attach_business_event(integration_id, component_id):
    """Attach an existing component to the integration's businessEvents socket."""
    res = requests.post(
        f"{BASE_URL}/v1/components/{integration_id}/settings/businessEvents/add-component",
        headers=_headers(),
        json={"source_component_id": component_id},
    )
    _raise(res)
    return res.json()


def detach_business_event(integration_id, component_id):
    """Remove a component from the integration's businessEvents socket."""
    res = requests.post(
        f"{BASE_URL}/v1/components/{integration_id}/settings/businessEvents/remove-component/{component_id}",
        headers=_headers(),
    )
    _raise(res)


def delete_component(component_id):
    """Delete a component entirely."""
    res = requests.delete(f"{BASE_URL}/v1/components/{component_id}", headers=_headers())
    _raise(res)
