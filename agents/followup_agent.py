"""
Uppföljningsagent — skapar och schemalägger uppföljningar med kunder och leads.
"""

import json
from datetime import datetime, timedelta
from typing import Optional
import anthropic
from anthropic import beta_tool

client = anthropic.Anthropic()

_followups: dict[str, dict] = {}


@beta_tool
def create_followup(
    lead_id: str,
    contact_name: str,
    channel: str,
    message: str,
    scheduled_date: str,
    priority: str = "normal",
) -> str:
    """Skapa en ny uppföljning för en lead eller kund.

    Args:
        lead_id: ID för leaden/kunden.
        contact_name: Kontaktpersonens namn.
        channel: Kanal för uppföljning: email, telefon, sms, möte.
        message: Meddelande eller samtalspunkter för uppföljningen.
        scheduled_date: Datum och tid för uppföljning (ISO-format YYYY-MM-DD HH:MM).
        priority: Prioritet: hög, normal, låg.
    """
    followup_id = f"FU-{len(_followups) + 1:04d}"
    _followups[followup_id] = {
        "id": followup_id,
        "lead_id": lead_id,
        "contact_name": contact_name,
        "channel": channel,
        "message": message,
        "scheduled_date": scheduled_date,
        "priority": priority,
        "status": "planerad",
        "created_at": datetime.now().isoformat(),
    }
    return json.dumps({
        "followup_id": followup_id,
        "message": f"Uppföljning skapad för {contact_name} den {scheduled_date} via {channel}.",
    })


@beta_tool
def generate_followup_message(
    contact_name: str,
    context: str,
    channel: str,
    tone: str = "professionell",
) -> str:
    """Generera ett personaliserat uppföljningsmeddelande.

    Args:
        contact_name: Mottagarens namn.
        context: Kontext om kontakten (t.ex. 'visade intresse för villa i Lidingö').
        channel: Kanal: email, sms, telefon.
        tone: Ton: professionell, vänlig, formell.
    """
    templates = {
        "email": f"Hej {contact_name},\n\nJag vill följa upp vår kontakt angående {context}.\n\nHör gärna av dig om du har frågor!\n\nMed vänliga hälsningar",
        "sms": f"Hej {contact_name}! Ville följa upp ang. {context}. Ring mig gärna 📱",
        "telefon": f"Samtalspunkter för {contact_name}: Referera till {context}. Fråga om intresset kvarstår. Erbjud nästa steg.",
    }
    msg = templates.get(channel, templates["email"])
    return json.dumps({"channel": channel, "contact_name": contact_name, "draft": msg, "tone": tone})


@beta_tool
def complete_followup(followup_id: str, outcome: str, notes: Optional[str] = None) -> str:
    """Markera en uppföljning som genomförd.

    Args:
        followup_id: Uppföljnings-ID.
        outcome: Utfall: positiv, neutral, negativ, inget_svar.
        notes: Anteckningar från uppföljningen (valfritt).
    """
    if followup_id not in _followups:
        return json.dumps({"error": f"Uppföljning {followup_id} hittades inte."})
    _followups[followup_id]["status"] = "genomförd"
    _followups[followup_id]["outcome"] = outcome
    _followups[followup_id]["notes"] = notes
    _followups[followup_id]["completed_at"] = datetime.now().isoformat()
    return json.dumps({"followup_id": followup_id, "outcome": outcome, "status": "genomförd"})


@beta_tool
def list_upcoming_followups(days_ahead: int = 7) -> str:
    """Lista kommande uppföljningar inom ett visst antal dagar.

    Args:
        days_ahead: Antal dagar framåt att lista (standard: 7).
    """
    now = datetime.now()
    cutoff = now + timedelta(days=days_ahead)
    upcoming = []
    for fu in _followups.values():
        if fu["status"] == "planerad":
            try:
                scheduled = datetime.fromisoformat(fu["scheduled_date"])
                if now <= scheduled <= cutoff:
                    upcoming.append(fu)
            except ValueError:
                upcoming.append(fu)
    upcoming.sort(key=lambda x: x.get("scheduled_date", ""))
    return json.dumps({"count": len(upcoming), "followups": upcoming})


@beta_tool
def get_followup_history(lead_id: str) -> str:
    """Hämta hela uppföljningshistoriken för en lead.

    Args:
        lead_id: Lead-ID att hämta historik för.
    """
    history = [fu for fu in _followups.values() if fu["lead_id"] == lead_id]
    history.sort(key=lambda x: x.get("created_at", ""))
    return json.dumps({"lead_id": lead_id, "count": len(history), "history": history})


class FollowupAgent:
    """Agent för att planera och genomföra uppföljningar."""

    SYSTEM = """Du är en uppföljningsagent för ett fastighetsbolag.
Din uppgift är att skapa personaliserade uppföljningar, schemalägga kontakter
och följa upp leads och kunder på ett strukturerat sätt.

Prioritera alltid uppföljningar med hög potential och håll en varm,
professionell ton i all kommunikation. Kommunicera på svenska."""

    def run(self, user_message: str) -> str:
        """Kör agenten med ett meddelande och returnera svaret."""
        runner = client.beta.messages.tool_runner(
            model="claude-opus-4-7",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=self.SYSTEM,
            tools=[
                create_followup,
                generate_followup_message,
                complete_followup,
                list_upcoming_followups,
                get_followup_history,
            ],
            messages=[{"role": "user", "content": user_message}],
        )
        response_text = ""
        for message in runner:
            for block in message.content:
                if hasattr(block, "text"):
                    response_text = block.text
        return response_text
