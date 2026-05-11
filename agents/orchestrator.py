"""
Orchestratoragent — koordinerar de fem specialistagenternas samarbete.
"""

import anthropic
from anthropic import beta_tool

from .leads_agent import LeadsAgent
from .followup_agent import FollowupAgent
from .document_agent import DocumentAgent
from .showing_agent import ShowingAgent
from .meeting_agent import MeetingAgent

client = anthropic.Anthropic()

_leads_agent = LeadsAgent()
_followup_agent = FollowupAgent()
_document_agent = DocumentAgent()
_showing_agent = ShowingAgent()
_meeting_agent = MeetingAgent()


@beta_tool
def delegate_to_leads_agent(instruction: str) -> str:
    """Skicka en uppgift till leadsagenten.
    Använd för: skapa leads, poängsätta leads, uppdatera leadstatus, lista eller hämta leads.

    Args:
        instruction: Tydlig instruktion på svenska om vad leadsagenten ska göra.
    """
    return _leads_agent.run(instruction)


@beta_tool
def delegate_to_followup_agent(instruction: str) -> str:
    """Skicka en uppgift till uppföljningsagenten.
    Använd för: skapa uppföljningar, generera meddelanden, markera uppföljningar klara, lista kommande uppföljningar.

    Args:
        instruction: Tydlig instruktion på svenska om vad uppföljningsagenten ska göra.
    """
    return _followup_agent.run(instruction)


@beta_tool
def delegate_to_document_agent(instruction: str) -> str:
    """Skicka en uppgift till dokumentagenten.
    Använd för: skapa dokument, analysera dokument, slutföra dokument, lista dokument.

    Args:
        instruction: Tydlig instruktion på svenska om vad dokumentagenten ska göra.
    """
    return _document_agent.run(instruction)


@beta_tool
def delegate_to_showing_agent(instruction: str) -> str:
    """Skicka en uppgift till visningsagenten.
    Använd för: boka visningar, registrera deltagare, förbereda visningsunderlag, markera visningar genomförda.

    Args:
        instruction: Tydlig instruktion på svenska om vad visningsagenten ska göra.
    """
    return _showing_agent.run(instruction)


@beta_tool
def delegate_to_meeting_agent(instruction: str) -> str:
    """Skicka en uppgift till mötesbokningsagenten.
    Använd för: lista lediga tider, boka möten, avboka eller omboka möten, lista bokade möten.

    Args:
        instruction: Tydlig instruktion på svenska om vad mötesbokningsagenten ska göra.
    """
    return _meeting_agent.run(instruction)


class OrchestratorAgent:
    """Koordinerar alla fem agenter och delegerar uppgifter till rätt specialist."""

    SYSTEM = """Du är en orchestratoragent för ett fastighetsbolag.
Du koordinerar ett team av fem specialistagenter:

1. Leadsagent — hanterar potentiella kunder: skapa, poängsätta och uppdatera leads
2. Uppföljningsagent — planerar och genomför uppföljningar via email, sms och telefon
3. Dokumentagent — skapar och granskar fastighetsdokument och avtal
4. Visningsagent — bokar och administrerar fastighetsvisningar
5. Mötesbokningsagent — bokar möten i kalendern med kunder och mäklare

När du får en uppgift:
- Analysera vad som behöver göras
- Delegera till rätt agent(er) i rätt ordning
- Sammanfatta resultaten för användaren på ett tydligt sätt
- Om en uppgift kräver flera agenter, kör dem i logisk ordning och passa vidare
  relevant information (t.ex. lead-ID, visnings-ID) mellan stegen

Kommunicera på svenska och ge alltid en tydlig sammanfattning av vad som gjorts."""

    def run(self, user_message: str) -> str:
        """Kör orchestratorn med ett meddelande och returnera det samlade svaret."""
        runner = client.beta.messages.tool_runner(
            model="claude-opus-4-7",
            max_tokens=8192,
            thinking={"type": "adaptive"},
            system=self.SYSTEM,
            tools=[
                delegate_to_leads_agent,
                delegate_to_followup_agent,
                delegate_to_document_agent,
                delegate_to_showing_agent,
                delegate_to_meeting_agent,
            ],
            messages=[{"role": "user", "content": user_message}],
        )
        response_text = ""
        for message in runner:
            for block in message.content:
                if hasattr(block, "text"):
                    response_text = block.text
        return response_text
