"""Sample agent capability requests for the Agent Factory Orchestrator."""

SAMPLE_REQUESTS = {
    "ecommerce_support": (
        "Build an AI customer support agent for an e-commerce platform. It should "
        "answer order status questions, handle returns and refunds, recommend "
        "products, and escalate to a human when it detects frustration or a policy "
        "exception. It must integrate with our orders API and knowledge base, keep "
        "latency under 3 seconds for typical replies, and never promise refunds "
        "outside policy."
    ),
    "research_assistant": (
        "Build a multi-agent research assistant that takes a research question, "
        "plans sub-questions, searches the web and internal documents, synthesizes "
        "findings with citations, and produces a fact-checked report."
    ),
    "devops_incident": (
        "Build an autonomous DevOps incident-response agent that triages alerts, "
        "correlates logs and metrics, proposes remediations, and can execute "
        "approved runbooks with human-in-the-loop sign-off for destructive actions."
    ),
    "contract_review": (
        "Build a legal contract-review agent for an in-house legal team that flags "
        "risky clauses, compares against our playbook, suggests redlines, and "
        "produces a risk summary. It must cite the exact clause and never give "
        "definitive legal advice."
    ),
}

DEFAULT_REQUEST = SAMPLE_REQUESTS["ecommerce_support"]
