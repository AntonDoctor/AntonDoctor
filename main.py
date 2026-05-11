"""
AntonDoctor — demo av orchestratoragenten som koordinerar alla fem specialistagenter.
"""

from dotenv import load_dotenv

load_dotenv()

from agents import OrchestratorAgent


def main() -> None:
    agent = OrchestratorAgent()

    print("AntonDoctor — Orchestratoragent demo")
    print("=" * 60)

    # Scenario 1: Ny lead + uppföljning + möte i ett svep
    print("\nScenario 1: Ny lead inkommer")
    print("-" * 60)
    response = agent.run(
        "Vi har fått en ny lead: Erik Lindqvist, telefon 070-1234567, "
        "erik@example.com. Han är intresserad av att köpa en villa i Bromma "
        "med budget 8 miljoner kronor. "
        "1) Skapa leaden och sätt ett poängvärde. "
        "2) Schemalägg en uppföljning via email till imorgon kl 09:00. "
        "3) Boka ett rådgivningsmöte med mäklaren Anna Bergström på första "
        "lediga tid."
    )
    print(response)

    # Scenario 2: Boka visning + skapa dokument
    print("\n\nScenario 2: Förbered en fastighetsaffär")
    print("-" * 60)
    response = agent.run(
        "Vi ska sälja Björkvägen 12 i Bromma, 180 kvm villa, pris 7,5 mkr, "
        "säljare Maria Hansson, ansvarig mäklare Anna Bergström. "
        "1) Boka en visning nästa lördag kl 13:00 i 60 minuter, max 15 deltagare. "
        "2) Registrera Erik Lindqvist (070-1234567, erik@example.com) till visningen. "
        "3) Skapa ett uppdragsavtal för säljaren och analysera det."
    )
    print(response)

    # Scenario 3: Fri text — orchestratorn bestämmer själv
    print("\n\nScenario 3: Fri förfrågan")
    print("-" * 60)
    response = agent.run(
        "Ge mig en statusöversikt: lista alla leads, kommande uppföljningar "
        "de nästa 7 dagarna, och bokade möten."
    )
    print(response)

    print("\n" + "=" * 60)
    print("Demo klar.")


if __name__ == "__main__":
    main()
