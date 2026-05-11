"""
Dokumentagent — hanterar skapande och analys av fastighetsdokument.
"""

import json
from datetime import datetime
from typing import Optional
import anthropic
from anthropic import beta_tool

client = anthropic.Anthropic()

_documents: dict[str, dict] = {}


@beta_tool
def create_document(
    doc_type: str,
    title: str,
    parties: str,
    content: str,
    property_address: Optional[str] = None,
) -> str:
    """Skapa ett nytt fastighetsdokument.

    Args:
        doc_type: Dokumenttyp: budgivning, intresseanmälan, uppdragsavtal, visningsbekräftelse, köpeavtal_utkast.
        title: Dokumentets titel.
        parties: Inblandade parter (t.ex. 'Köpare: Anna Svensson, Säljare: Lars Karlsson').
        content: Dokumentets innehåll.
        property_address: Fastighetens adress (valfritt).
    """
    doc_id = f"DOC-{len(_documents) + 1:04d}"
    _documents[doc_id] = {
        "id": doc_id,
        "type": doc_type,
        "title": title,
        "parties": parties,
        "content": content,
        "property_address": property_address,
        "status": "utkast",
        "version": 1,
        "created_at": datetime.now().isoformat(),
    }
    return json.dumps({
        "doc_id": doc_id,
        "message": f"Dokument '{title}' (ID: {doc_id}) skapat som utkast.",
    })


@beta_tool
def analyze_document(doc_id: str) -> str:
    """Analysera ett dokument och identifiera nyckelinformation och eventuella problem.

    Args:
        doc_id: Dokument-ID att analysera.
    """
    if doc_id not in _documents:
        return json.dumps({"error": f"Dokument {doc_id} hittades inte."})
    doc = _documents[doc_id]
    # Simplified analysis — a real implementation would use NLP
    word_count = len(doc["content"].split())
    has_parties = bool(doc["parties"])
    has_address = bool(doc.get("property_address"))
    issues = []
    if not has_parties:
        issues.append("Parter saknas i dokumentet.")
    if not has_address and doc["type"] in {"köpeavtal_utkast", "uppdragsavtal"}:
        issues.append("Fastighetsadress saknas.")
    if word_count < 50:
        issues.append("Dokumentet verkar vara mycket kort — kontrollera att allt innehåll är med.")
    return json.dumps({
        "doc_id": doc_id,
        "title": doc["title"],
        "type": doc["type"],
        "word_count": word_count,
        "parties_present": has_parties,
        "address_present": has_address,
        "potential_issues": issues,
        "overall": "OK" if not issues else "Kräver granskning",
    })


@beta_tool
def finalize_document(doc_id: str) -> str:
    """Markera ett dokument som färdigt (inte längre ett utkast).

    Args:
        doc_id: Dokument-ID att slutföra.
    """
    if doc_id not in _documents:
        return json.dumps({"error": f"Dokument {doc_id} hittades inte."})
    _documents[doc_id]["status"] = "färdigt"
    _documents[doc_id]["finalized_at"] = datetime.now().isoformat()
    return json.dumps({"doc_id": doc_id, "status": "färdigt"})


@beta_tool
def list_documents(doc_type: Optional[str] = None, status: Optional[str] = None) -> str:
    """Lista alla dokument, eventuellt filtrerade.

    Args:
        doc_type: Filtrera på typ (valfritt).
        status: Filtrera på status: utkast, färdigt (valfritt).
    """
    docs = list(_documents.values())
    if doc_type:
        docs = [d for d in docs if d["type"] == doc_type]
    if status:
        docs = [d for d in docs if d["status"] == status]
    docs.sort(key=lambda d: d["created_at"], reverse=True)
    # Return summary without full content to keep response lean
    summaries = [
        {k: v for k, v in d.items() if k != "content"}
        for d in docs
    ]
    return json.dumps({"count": len(summaries), "documents": summaries})


@beta_tool
def get_document(doc_id: str) -> str:
    """Hämta ett specifikt dokument med fullt innehåll.

    Args:
        doc_id: Dokument-ID att hämta.
    """
    if doc_id not in _documents:
        return json.dumps({"error": f"Dokument {doc_id} hittades inte."})
    return json.dumps(_documents[doc_id])


class DocumentAgent:
    """Agent för att hantera fastighetsdokument."""

    SYSTEM = """Du är en dokumentagent för ett fastighetsbolag.
Din uppgift är att skapa, granska och hantera alla typer av fastighetsdokument:
uppdragsavtal, köpeavtal, intresseanmälningar, budgivningsdokument och mer.

Var noggrann med detaljer — ett fel i ett fastighetsdokument kan få stora konsekvenser.
Se alltid till att parter, adresser och belopp är korrekt angivna.
Kommunicera på svenska."""

    def run(self, user_message: str) -> str:
        """Kör agenten med ett meddelande och returnera svaret."""
        runner = client.beta.messages.tool_runner(
            model="claude-opus-4-7",
            max_tokens=8192,
            thinking={"type": "adaptive"},
            system=self.SYSTEM,
            tools=[
                create_document,
                analyze_document,
                finalize_document,
                list_documents,
                get_document,
            ],
            messages=[{"role": "user", "content": user_message}],
        )
        response_text = ""
        for message in runner:
            for block in message.content:
                if hasattr(block, "text"):
                    response_text = block.text
        return response_text
