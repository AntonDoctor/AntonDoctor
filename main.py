"""
AntonDoctor — demo av alla fem AI-agenter för fastighetsbranschen.
"""

from dotenv import load_dotenv

load_dotenv()

from agents import LeadsAgent, FollowupAgent, DocumentAgent, ShowingAgent, MeetingAgent


def demo_leads_agent() -> None:
    print("\n" + "=" * 60)
    print("LEADSAGENT")
    print("=" * 60)
    agent = LeadsAgent()
    response = agent.run(
        "Vi har fått in en ny lead: Erik Lindqvist, telefon 070-1234567, "
        "erik@example.com. Han är intresserad av att köpa en villa i Bromma "
        "med budget 8 miljoner kronor. Skapa leaden och sätt ett lämpligt "
        "poängvärde baserat på informationen."
    )
    print(response)


def demo_followup_agent() -> None:
    print("\n" + "=" * 60)
    print("UPPFÖLJNINGSAGENT")
    print("=" * 60)
    agent = FollowupAgent()
    response = agent.run(
        "Skapa en uppföljning för lead LEAD-0001 (Erik Lindqvist) via e-post. "
        "Han visade intresse för villaköp i Bromma förra veckan men vi har inte "
        "hört av oss sedan dess. Schemalägg uppföljningen till imorgon kl 09:00 "
        "och generera ett lämpligt meddelande med professionell ton."
    )
    print(response)


def demo_document_agent() -> None:
    print("\n" + "=" * 60)
    print("DOKUMENTAGENT")
    print("=" * 60)
    agent = DocumentAgent()
    response = agent.run(
        "Skapa ett utkast till uppdragsavtal för säljaren Maria Hansson "
        "gällande fastigheten Björkvägen 12, 168 55 Bromma. "
        "Avtalet gäller försäljning av en villa på 180 kvm, "
        "beräknat marknadsvärde 7,5 miljoner kronor. "
        "Ansvarig mäklare är Anna Bergström. "
        "Analysera sedan dokumentet och kontrollera att allt är i ordning."
    )
    print(response)


def demo_showing_agent() -> None:
    print("\n" + "=" * 60)
    print("VISNINGSAGENT")
    print("=" * 60)
    agent = ShowingAgent()
    response = agent.run(
        "Boka en visning för Björkvägen 12 i Bromma nästa lördag kl 13:00, "
        "60 minuter lång, ansvarig mäklare Anna Bergström, max 15 deltagare. "
        "Registrera sedan Erik Lindqvist (070-1234567, erik@example.com) som deltagare. "
        "Förbered också ett visningsunderlag — fastigheten är en villa på 180 kvm, "
        "5 rum, renoverat kök 2022, stor trädgård, pris 7,5 mkr."
    )
    print(response)


def demo_meeting_agent() -> None:
    print("\n" + "=" * 60)
    print("MÖTESBOKNINGSAGENT")
    print("=" * 60)
    agent = MeetingAgent()
    response = agent.run(
        "Visa tillgängliga mötestider för de kommande 5 dagarna. "
        "Boka sedan ett rådgivningsmöte med Erik Lindqvist "
        "(telefon 070-1234567, erik@example.com) hos mäklaren Anna Bergström. "
        "Välj den första lämpliga lediga tiden. "
        "Mötet gäller genomgång av köpprocessen och visningsutfall."
    )
    print(response)


if __name__ == "__main__":
    print("AntonDoctor — AI-agenter för fastighetsbranschen")
    print("Kör demo av alla fem agenter...\n")

    demo_leads_agent()
    demo_followup_agent()
    demo_document_agent()
    demo_showing_agent()
    demo_meeting_agent()

    print("\n" + "=" * 60)
    print("Demo klar.")
