#!/usr/bin/env python3
"""
Extole SFDC Integration Component CLI

Simulates the SFDC event configurator to exercise the Extole Component API.

Usage:
  python cli/main.py show
  python cli/main.py list
  python cli/main.py add <event_name> [ADVOCATE|FRIEND]
  python cli/main.py remove <event_name>
  python cli/main.py setup              # create integration + campaign (one-time per tenant)
"""

import sys
import json
import client


def cmd_show():
    """Show the Salesforce integration component."""
    integration = client.find_salesforce_integration()
    if not integration:
        print("No 'salesforce' integration-v10.0 found. Run 'setup' first.")
        return
    print(json.dumps(integration, indent=2))


def cmd_list():
    """List all business events installed on the Salesforce integration."""
    integration = client.find_salesforce_integration()
    if not integration:
        print("No 'salesforce' integration-v10.0 found. Run 'setup' first.")
        return

    events = client.list_business_events(integration["id"])
    if not events:
        print("No business events installed.")
        return

    print(f"Business events on Salesforce integration ({integration['id']}):")
    for e in events:
        print(f"  {e.get('name'):40s}  id={e.get('id')}")


def cmd_add(event_name, journey_name="ADVOCATE"):
    """Create a business-event component and attach it to the Salesforce integration."""
    if journey_name.upper() not in ("ADVOCATE", "FRIEND"):
        print(f"journey must be ADVOCATE or FRIEND, got '{journey_name}'")
        sys.exit(1)

    integration = client.find_salesforce_integration()
    if not integration:
        print("No 'salesforce' integration-v10.0 found. Run 'setup' first.")
        sys.exit(1)

    integration_id = integration["id"]
    campaign_id    = integration["campaign_id"]

    existing = client.find_business_event(integration_id, event_name)
    if existing:
        print(f"Business event '{event_name}' already exists (id={existing['id']}). Nothing to do.")
        return

    print(f"Creating business event '{event_name}' (journey={journey_name})...")
    component = client.create_business_event(event_name, campaign_id, journey_name.upper())
    component_id = component["id"]
    print(f"  Created: id={component_id}")

    print(f"Attaching to integration via businessEvents socket...")
    client.attach_business_event(integration_id, component_id)
    print(f"  Done. '{event_name}' is now visible in FlowBuilder.")


def cmd_remove(event_name):
    """Detach and delete a business-event component from the Salesforce integration."""
    integration = client.find_salesforce_integration()
    if not integration:
        print("No 'salesforce' integration-v10.0 found.")
        sys.exit(1)

    integration_id = integration["id"]

    existing = client.find_business_event(integration_id, event_name)
    if not existing:
        print(f"Business event '{event_name}' not found on this integration.")
        return

    installed_id = existing["id"]
    print(f"Detaching '{event_name}' (installed id={installed_id})...")
    source_id = client.detach_business_event(integration_id, installed_id)

    if source_id:
        print(f"Deleting source component (id={source_id})...")
        try:
            client.delete_component(source_id)
        except RuntimeError as e:
            print(f"  Warning: {e}")
    print(f"  Done.")


def cmd_setup():
    """Create the Salesforce integration campaign and component (one-time per tenant)."""
    existing = client.find_salesforce_integration()
    if existing:
        print(f"Salesforce integration already exists (id={existing['id']}). Nothing to do.")
        return

    print("Creating campaign 'Salesforce'...")
    campaign = client.create_campaign(
        "Salesforce",
        "Salesforce CRM integration — houses the event catalog for FlowBuilder"
    )
    campaign_id = campaign["campaign_id"]
    print(f"  Campaign id={campaign_id}")

    print("Creating salesforce integration-v10.0 component...")
    integration = client.create_salesforce_integration(campaign_id)
    print(f"  Integration id={integration['id']}")
    print("  Done. Ready to add events with 'add <event_name>'.")


COMMANDS = {
    "show":   (cmd_show,   0),
    "list":   (cmd_list,   0),
    "add":    (cmd_add,    None),  # 1 or 2 args
    "remove": (cmd_remove, 1),
    "setup":  (cmd_setup,  0),
}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] not in COMMANDS:
        print(__doc__)
        sys.exit(1)

    cmd, arity = COMMANDS[args[0]]
    rest = args[1:]
    if arity is not None and len(rest) != arity:
        print(f"'{args[0]}' requires {arity} argument(s), got {len(rest)}.")
        sys.exit(1)

    try:
        cmd(*rest)
    except RuntimeError as e:
        print(f"API error: {e}")
        sys.exit(1)
