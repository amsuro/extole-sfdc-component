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


# ── Integration discovery ──────────────────────────────────────────────────────

def find_salesforce_integration():
    """Return the component dict for the 'salesforce' integration-v10.0, or None."""
    res = requests.get(
        f"{BASE_URL}/v1/components",
        headers=_headers(),
        params={"havingAnyTypes": "integration-v10.0"},
    )
    _raise(res)
    for c in res.json():
        if c.get("name") == "salesforce":
            return c
    return None


# ── Business event socket ──────────────────────────────────────────────────────

def list_business_events(integration_id):
    """Return list of installed business-event components on the integration."""
    res = requests.get(
        f"{BASE_URL}/v1/components/{integration_id}/settings/businessEvent/installed-components",
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


def create_business_event(event_name):
    """Create a business-event-v10.0 component at account level. Returns the component dict."""
    singular, plural, rate = _derive_display_names(event_name)
    payload = {
        "name":  event_name,
        "types": ["business-event-v10.0"],
        "settings": [
            {"name": "singularNounName",  "values": {"default": singular}},
            {"name": "pluralNounName",    "values": {"default": plural}},
            {"name": "rateName",          "values": {"default": rate}},
            {"name": "dataCapturePolicy", "values": {"default": "ALL_DATA"}},
            {"name": "dataCopyScope",     "values": {"default": "PRIVATE"}},
            {"name": "journeyName",       "values": {"default": "ADVOCATE"}},
            {"name": "adminUIIcon",       "values": {"default": "far fa-cloud"}},
            {"name": "adminUIColor",      "values": {"default": "#00A1E0"}},
        ],
    }
    res = requests.post(f"{BASE_URL}/v1/components", headers=_headers(), json=payload)
    _raise(res)
    return res.json()


def attach_business_event(integration_id, component_id):
    """Attach an existing component to the integration's businessEvent socket."""
    res = requests.post(
        f"{BASE_URL}/v1/components/{integration_id}/settings/businessEvent/add-component",
        headers=_headers(),
        json={"component_id": component_id},
    )
    _raise(res)
    return res.json()


def detach_business_event(integration_id, component_id):
    """Remove a component from the integration's businessEvent socket."""
    res = requests.post(
        f"{BASE_URL}/v1/components/{integration_id}/settings/businessEvent/remove-component/{component_id}",
        headers=_headers(),
    )
    _raise(res)


def delete_component(component_id):
    """Delete a component entirely."""
    res = requests.delete(f"{BASE_URL}/v1/components/{component_id}", headers=_headers())
    _raise(res)
