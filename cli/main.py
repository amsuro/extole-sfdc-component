#!/usr/bin/env python3
"""
Extole SFDC Integration Component CLI

Simulates the SFDC event configurator to exercise the Extole Component API.

Usage:
  python cli/main.py list
  python cli/main.py add <event_name>
  python cli/main.py remove <event_name>
  python cli/main.py show
"""

import sys
import json
import client


def cmd_show():
    """Show the Salesforce integration component."""
    integration = client.find_salesforce_integration()
    if not integration:
        print("No 'salesforce' integration-v10.0 found in this account.")
        return
    print(json.dumps(integration, indent=2))


def cmd_list():
    """List all business events installed on the Salesforce integration."""
    integration = client.find_salesforce_integration()
    if not integration:
        print("No 'salesforce' integration-v10.0 found in this account.")
        return

    events = client.list_business_events(integration["id"])
    if not events:
        print("No business events installed.")
        return

    print(f"Business events on integration '{integration['id']}':")
    for e in events:
        print(f"  {e.get('name'):40s}  id={e.get('id')}")


def cmd_add(event_name):
    """Create a business-event component and attach it to the Salesforce integration."""
    integration = client.find_salesforce_integration()
    if not integration:
        print("No 'salesforce' integration-v10.0 found. Has it been created in this account?")
        sys.exit(1)

    integration_id = integration["id"]

    existing = client.find_business_event(integration_id, event_name)
    if existing:
        print(f"Business event '{event_name}' already exists (id={existing['id']}). Nothing to do.")
        return

    print(f"Creating business event component '{event_name}'...")
    component = client.create_business_event(event_name)
    component_id = component["id"]
    print(f"  Created: id={component_id}")

    print(f"Attaching to integration '{integration_id}' via businessEvent socket...")
    client.attach_business_event(integration_id, component_id)
    print(f"  Done. '{event_name}' is now active in FlowBuilder.")


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

    component_id = existing["id"]
    print(f"Detaching '{event_name}' (id={component_id}) from integration...")
    client.detach_business_event(integration_id, component_id)
    print(f"Deleting component...")
    client.delete_component(component_id)
    print(f"  Done. '{event_name}' removed.")


COMMANDS = {
    "show":   (cmd_show,   0),
    "list":   (cmd_list,   0),
    "add":    (cmd_add,    1),
    "remove": (cmd_remove, 1),
}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] not in COMMANDS:
        print(__doc__)
        sys.exit(1)

    cmd, arity = COMMANDS[args[0]]
    rest = args[1:]
    if len(rest) != arity:
        print(f"'{args[0]}' requires {arity} argument(s), got {len(rest)}.")
        sys.exit(1)

    try:
        cmd(*rest)
    except RuntimeError as e:
        print(f"API error: {e}")
        sys.exit(1)
