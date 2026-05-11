"""
Visningsagent — hanterar och förbereder fastighetsvisningar.
"""

import json
from datetime import datetime
from typing import Optional
import anthropic
from anthropic import beta_tool

client = anthropic.Anthropic()

_showings: dict[str, dict] = {}


@beta_tool
def schedule_showing(
    property_address: str,
    date: str,
    time: str,
    duration_minutes: int,
    agent_name: str,
    max_attendees: int = 20,
    notes: Optional[str] = None,
) -> str:
    """Boka en ny fastighetsvisning.

    Args:
        property_address: Fastighetens adress.
        date: Datum för visningen (YYYY-MM-DD).
        time: Klockslag (HH:MM).
        duration_minutes: Beräknad visningstid i minuter.
        agent_name: Ansvarig mäklares namn.
        max_attendees: Max antal deltagare (standard: 20).
        notes: Extra anteckningar (valfritt).
    """
    showing_id = f"VIS-{len(_showings) + 1:04d}"
    _showings[showing_id] = {
        "id": showing_id,
        "property_address": property_address,
        "date": date,
        "time": time,
        "duration_minutes": duration_minutes,
        "agent_name": agent_name,
        "max_attendees": max_attendees,
        "registered_attendees": [],
        "notes": notes,
        "status": "planerad",
        "created_at": datetime.now().isoformat(),
    }
    return json.dumps({
        "showing_id": showing_id,
        "message": f"Visning bokad för {property_address} den {date} kl. {time}.",
    })


@beta_tool
def register_attendee(showing_id: str, name: str, phone: str, email: Optional[str] = None) -> str:
    """Registrera en deltagare till en visning.

    Args:
        showing_id: Visnings-ID.
        name: Deltagarens namn.
        phone: Telefonnummer.
        email: E-postadress (valfritt).
    """
    if showing_id not in _showings:
        return json.dumps({"error": f"Visning {showing_id} hittades inte."})
    showing = _showings[showing_id]
    if len(showing["registered_attendees"]) >= showing["max_attendees"]:
        return json.dumps({"error": "Visningen är fullbokad."})
    attendee = {"name": name, "phone": phone, "email": email, "registered_at": datetime.now().isoformat()}
    showing["registered_attendees"].append(attendee)
    spots_left = showing["max_attendees"] - len(showing["registered_attendees"])
    return json.dumps({
        "showing_id": showing_id,
        "attendee": name,
        "message": f"{name} är registrerad för visningen. {spots_left} platser kvar.",
    })


@beta_tool
def prepare_showing_brief(showing_id: str, property_info: str) -> str:
    """Skapa ett visningsunderlag med nyckelinformation om fastigheten.

    Args:
        showing_id: Visnings-ID att förbereda underlag för.
        property_info: Information om fastigheten (t.ex. storlek, pris, beskrivning).
    """
    if showing_id not in _showings:
        return json.dumps({"error": f"Visning {showing_id} hittades inte."})
    showing = _showings[showing_id]
    brief = {
        "showing_id": showing_id,
        "property": showing["property_address"],
        "datetime": f"{showing['date']} kl. {showing['time']}",
        "duration": f"{showing['duration_minutes']} minuter",
        "agent": showing["agent_name"],
        "registered": len(showing["registered_attendees"]),
        "max_attendees": showing["max_attendees"],
        "property_details": property_info,
        "talking_points": [
            "Berätta om läget och närmiljön",
            "Lyft fram fastighetens starkaste sidor",
            "Nämn genomförda renoveringar",
            "Förklara budgivningsprocessen",
            "Ge tid för frågor",
        ],
        "generated_at": datetime.now().isoformat(),
    }
    _showings[showing_id]["brief"] = brief
    return json.dumps(brief)


@beta_tool
def complete_showing(showing_id: str, outcome: str, interested_parties: Optional[str] = None) -> str:
    """Markera en visning som genomförd och registrera utfall.

    Args:
        showing_id: Visnings-ID.
        outcome: Utfall: positivt, neutralt, få_intressenter, inga_intressenter.
        interested_parties: Namn på eventuellt intresserade parter (valfritt).
    """
    if showing_id not in _showings:
        return json.dumps({"error": f"Visning {showing_id} hittades inte."})
    _showings[showing_id]["status"] = "genomförd"
    _showings[showing_id]["outcome"] = outcome
    _showings[showing_id]["interested_parties"] = interested_parties
    _showings[showing_id]["completed_at"] = datetime.now().isoformat()
    return json.dumps({"showing_id": showing_id, "status": "genomförd", "outcome": outcome})


@beta_tool
def list_showings(status_filter: Optional[str] = None, date_from: Optional[str] = None) -> str:
    """Lista visningar, eventuellt filtrerade.

    Args:
        status_filter: Filtrera på status: planerad, genomförd, inställd (valfritt).
        date_from: Visa visningar från och med detta datum YYYY-MM-DD (valfritt).
    """
    showings = list(_showings.values())
    if status_filter:
        showings = [s for s in showings if s["status"] == status_filter]
    if date_from:
        showings = [s for s in showings if s["date"] >= date_from]
    showings.sort(key=lambda s: (s["date"], s["time"]))
    return json.dumps({"count": len(showings), "showings": showings})


class ShowingAgent:
    """Agent för att planera och genomföra fastighetsvisningar."""

    SYSTEM = """Du är en visningsagent för ett fastighetsbolag.
Din uppgift är att planera, organisera och följa upp fastighetsvisningar.
Du hjälper till att boka visningar, registrera intressenter, förbereda visningsunderlag
och dokumentera utfall.

Var serviceinriktad och se till att varje visning är välplanerad och professionellt genomförd.
Kommunicera på svenska."""

    def run(self, user_message: str) -> str:
        """Kör agenten med ett meddelande och returnera svaret."""
        runner = client.beta.messages.tool_runner(
            model="claude-opus-4-7",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=self.SYSTEM,
            tools=[
                schedule_showing,
                register_attendee,
                prepare_showing_brief,
                complete_showing,
                list_showings,
            ],
            messages=[{"role": "user", "content": user_message}],
        )
        response_text = ""
        for message in runner:
            for block in message.content:
                if hasattr(block, "text"):
                    response_text = block.text
        return response_text
