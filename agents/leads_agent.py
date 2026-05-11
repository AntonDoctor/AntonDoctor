"""
Leadsagent — kvalificerar och hanterar potentiella kunder.
"""

import json
from datetime import datetime
from typing import Optional
import anthropic
from anthropic import beta_tool

client = anthropic.Anthropic()

# In-memory lead storage (replace with a real database in production)
_leads: dict[str, dict] = {}


@beta_tool
def qualify_lead(
    name: str,
    phone: str,
    email: str,
    interest: str,
    budget: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """Skapa och kvalificera en ny lead. Returnerar lead-ID.

    Args:
        name: Leadsens fullständiga namn.
        phone: Telefonnummer.
        email: E-postadress.
        interest: Vad leaden är intresserad av (t.ex. 'köpa villa', 'sälja lägenhet').
        budget: Budget i kronor (valfritt).
        notes: Extra anteckningar (valfritt).
    """
    lead_id = f"LEAD-{len(_leads) + 1:04d}"
    _leads[lead_id] = {
        "id": lead_id,
        "name": name,
        "phone": phone,
        "email": email,
        "interest": interest,
        "budget": budget,
        "notes": notes,
        "status": "ny",
        "score": None,
        "created_at": datetime.now().isoformat(),
    }
    return json.dumps({"lead_id": lead_id, "message": f"Lead '{name}' skapad med ID {lead_id}."})


@beta_tool
def score_lead(lead_id: str, score: int, motivation: str) -> str:
    """Sätt ett poängvärde (1–10) på en lead baserat på kvalitet.

    Args:
        lead_id: Lead-ID att poängsätta.
        score: Poäng 1–10 (10 = varm/klar att köpa, 1 = kall).
        motivation: Motivering till poängen.
    """
    if lead_id not in _leads:
        return json.dumps({"error": f"Lead {lead_id} hittades inte."})
    _leads[lead_id]["score"] = score
    _leads[lead_id]["score_motivation"] = motivation
    _leads[lead_id]["scored_at"] = datetime.now().isoformat()
    label = "varm 🔥" if score >= 7 else "ljummen 🌡️" if score >= 4 else "kall ❄️"
    return json.dumps({"lead_id": lead_id, "score": score, "label": label})


@beta_tool
def update_lead_status(lead_id: str, new_status: str) -> str:
    """Uppdatera status på en lead.

    Args:
        lead_id: Lead-ID.
        new_status: Ny status — ett av: ny, kontaktad, kvalificerad, förlorad, kund.
    """
    allowed = {"ny", "kontaktad", "kvalificerad", "förlorad", "kund"}
    if new_status not in allowed:
        return json.dumps({"error": f"Ogiltigt status. Välj ett av: {allowed}"})
    if lead_id not in _leads:
        return json.dumps({"error": f"Lead {lead_id} hittades inte."})
    _leads[lead_id]["status"] = new_status
    _leads[lead_id]["updated_at"] = datetime.now().isoformat()
    return json.dumps({"lead_id": lead_id, "status": new_status})


@beta_tool
def list_leads(status_filter: Optional[str] = None) -> str:
    """Lista alla leads, eventuellt filtrerade på status.

    Args:
        status_filter: Filtrera på status (valfritt): ny, kontaktad, kvalificerad, förlorad, kund.
    """
    leads = list(_leads.values())
    if status_filter:
        leads = [l for l in leads if l["status"] == status_filter]
    # Sortera efter score (högt first), sedan datum
    leads.sort(key=lambda l: (-(l.get("score") or 0), l["created_at"]))
    return json.dumps({"count": len(leads), "leads": leads})


@beta_tool
def get_lead(lead_id: str) -> str:
    """Hämta detaljer om en specifik lead.

    Args:
        lead_id: Lead-ID att hämta.
    """
    if lead_id not in _leads:
        return json.dumps({"error": f"Lead {lead_id} hittades inte."})
    return json.dumps(_leads[lead_id])


class LeadsAgent:
    """Agent för att hantera och kvalificera leads."""

    SYSTEM = """Du är en professionell leadsagent för ett fastighetsbolag.
Din uppgift är att ta emot nya potentiella kunder (leads), samla information om dem,
kvalificera dem och hålla databasen uppdaterad.

Var alltid hjälpsam, strukturerad och affärsmässig.
Kommunicera på svenska om inte annat anges."""

    def run(self, user_message: str) -> str:
        """Kör agenten med ett meddelande och returnera svaret."""
        runner = client.beta.messages.tool_runner(
            model="claude-opus-4-7",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=self.SYSTEM,
            tools=[qualify_lead, score_lead, update_lead_status, list_leads, get_lead],
            messages=[{"role": "user", "content": user_message}],
        )
        response_text = ""
        for message in runner:
            for block in message.content:
                if hasattr(block, "text"):
                    response_text = block.text
        return response_text
