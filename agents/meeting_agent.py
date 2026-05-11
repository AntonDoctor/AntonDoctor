"""
Mötesbokningsagent — hanterar bokning och bekräftelse av kundmöten.
"""

import json
from datetime import datetime, timedelta
from typing import Optional
import anthropic
from anthropic import beta_tool

client = anthropic.Anthropic()

_meetings: dict[str, dict] = {}
_calendar_slots: list[dict] = []


def _seed_calendar_slots() -> None:
    """Generera tillgängliga mötestider för de kommande 14 dagarna."""
    if _calendar_slots:
        return
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for day_offset in range(1, 15):
        day = today + timedelta(days=day_offset)
        if day.weekday() < 5:  # Måndag–fredag
            for hour in [9, 10, 11, 13, 14, 15, 16]:
                _calendar_slots.append({
                    "date": day.strftime("%Y-%m-%d"),
                    "time": f"{hour:02d}:00",
                    "available": True,
                })


_seed_calendar_slots()


@beta_tool
def list_available_slots(date_from: Optional[str] = None, date_to: Optional[str] = None) -> str:
    """Lista tillgängliga mötestider.

    Args:
        date_from: Filtrera från detta datum YYYY-MM-DD (valfritt).
        date_to: Filtrera till detta datum YYYY-MM-DD (valfritt).
    """
    slots = [s for s in _calendar_slots if s["available"]]
    if date_from:
        slots = [s for s in slots if s["date"] >= date_from]
    if date_to:
        slots = [s for s in slots if s["date"] <= date_to]
    return json.dumps({"available_count": len(slots), "slots": slots[:20]})  # max 20 in response


@beta_tool
def book_meeting(
    client_name: str,
    client_phone: str,
    client_email: str,
    date: str,
    time: str,
    meeting_type: str,
    agenda: str,
    agent_name: str,
    location: Optional[str] = None,
) -> str:
    """Boka ett möte med en kund.

    Args:
        client_name: Kundens namn.
        client_phone: Kundens telefonnummer.
        client_email: Kundens e-postadress.
        date: Mötesdatum (YYYY-MM-DD).
        time: Mötestid (HH:MM).
        meeting_type: Mötestyp: rådgivning, värdering, genomgång, kontraktsskrivning, uppföljning.
        agenda: Mötets agenda/syfte.
        agent_name: Ansvarig mäklares namn.
        location: Plats för mötet (valfritt, t.ex. 'Kontoret, Storgatan 1' eller 'Digitalt via Teams').
    """
    # Check if slot is available
    slot = next(
        (s for s in _calendar_slots if s["date"] == date and s["time"] == time and s["available"]),
        None,
    )
    if not slot:
        return json.dumps({"error": f"Tidsluckan {date} kl. {time} är inte tillgänglig. Kontrollera tillgängliga tider."})

    meeting_id = f"MÖT-{len(_meetings) + 1:04d}"
    _meetings[meeting_id] = {
        "id": meeting_id,
        "client_name": client_name,
        "client_phone": client_phone,
        "client_email": client_email,
        "date": date,
        "time": time,
        "meeting_type": meeting_type,
        "agenda": agenda,
        "agent_name": agent_name,
        "location": location or "Kontoret",
        "status": "bekräftat",
        "created_at": datetime.now().isoformat(),
    }
    # Mark slot as unavailable
    slot["available"] = False

    confirmation = (
        f"✅ Möte bokat!\n"
        f"Kund: {client_name}\n"
        f"Datum: {date} kl. {time}\n"
        f"Typ: {meeting_type}\n"
        f"Plats: {location or 'Kontoret'}\n"
        f"Mäklare: {agent_name}\n"
        f"ID: {meeting_id}"
    )
    return json.dumps({"meeting_id": meeting_id, "confirmation": confirmation})


@beta_tool
def cancel_meeting(meeting_id: str, reason: Optional[str] = None) -> str:
    """Avboka ett bokat möte.

    Args:
        meeting_id: Mötes-ID att avboka.
        reason: Anledning till avbokning (valfritt).
    """
    if meeting_id not in _meetings:
        return json.dumps({"error": f"Möte {meeting_id} hittades inte."})
    meeting = _meetings[meeting_id]
    meeting["status"] = "avbokat"
    meeting["cancellation_reason"] = reason
    meeting["cancelled_at"] = datetime.now().isoformat()
    # Free up the slot
    for slot in _calendar_slots:
        if slot["date"] == meeting["date"] and slot["time"] == meeting["time"]:
            slot["available"] = True
            break
    return json.dumps({"meeting_id": meeting_id, "status": "avbokat", "reason": reason})


@beta_tool
def reschedule_meeting(meeting_id: str, new_date: str, new_time: str) -> str:
    """Omboka ett möte till en ny tid.

    Args:
        meeting_id: Mötes-ID att omboka.
        new_date: Nytt datum (YYYY-MM-DD).
        new_time: Ny tid (HH:MM).
    """
    if meeting_id not in _meetings:
        return json.dumps({"error": f"Möte {meeting_id} hittades inte."})
    new_slot = next(
        (s for s in _calendar_slots if s["date"] == new_date and s["time"] == new_time and s["available"]),
        None,
    )
    if not new_slot:
        return json.dumps({"error": f"Nya tidsluckan {new_date} kl. {new_time} är inte tillgänglig."})
    meeting = _meetings[meeting_id]
    # Free old slot
    for slot in _calendar_slots:
        if slot["date"] == meeting["date"] and slot["time"] == meeting["time"]:
            slot["available"] = True
            break
    # Book new slot
    new_slot["available"] = False
    old_datetime = f"{meeting['date']} kl. {meeting['time']}"
    meeting["date"] = new_date
    meeting["time"] = new_time
    meeting["rescheduled_from"] = old_datetime
    meeting["rescheduled_at"] = datetime.now().isoformat()
    return json.dumps({
        "meeting_id": meeting_id,
        "new_datetime": f"{new_date} kl. {new_time}",
        "message": f"Möte ombokat från {old_datetime} till {new_date} kl. {new_time}.",
    })


@beta_tool
def list_meetings(
    status_filter: Optional[str] = None,
    agent_name: Optional[str] = None,
    date_from: Optional[str] = None,
) -> str:
    """Lista bokade möten.

    Args:
        status_filter: Filtrera på status: bekräftat, avbokat, genomfört (valfritt).
        agent_name: Filtrera på mäklare (valfritt).
        date_from: Visa möten från detta datum YYYY-MM-DD (valfritt).
    """
    meetings = list(_meetings.values())
    if status_filter:
        meetings = [m for m in meetings if m["status"] == status_filter]
    if agent_name:
        meetings = [m for m in meetings if agent_name.lower() in m["agent_name"].lower()]
    if date_from:
        meetings = [m for m in meetings if m["date"] >= date_from]
    meetings.sort(key=lambda m: (m["date"], m["time"]))
    return json.dumps({"count": len(meetings), "meetings": meetings})


class MeetingAgent:
    """Agent för att boka och hantera kundmöten."""

    SYSTEM = """Du är en mötesbokningsagent för ett fastighetsbolag.
Din uppgift är att boka möten med kunder och leads, hantera kalender och
skicka bekräftelser. Du ser till att rätt mäklare möter rätt kund vid rätt tillfälle.

Var effektiv och tydlig. Kontrollera alltid att önskad tid är tillgänglig innan du bokar.
Kommunicera på svenska."""

    def run(self, user_message: str) -> str:
        """Kör agenten med ett meddelande och returnera svaret."""
        runner = client.beta.messages.tool_runner(
            model="claude-opus-4-7",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=self.SYSTEM,
            tools=[
                list_available_slots,
                book_meeting,
                cancel_meeting,
                reschedule_meeting,
                list_meetings,
            ],
            messages=[{"role": "user", "content": user_message}],
        )
        response_text = ""
        for message in runner:
            for block in message.content:
                if hasattr(block, "text"):
                    response_text = block.text
        return response_text
