from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_settings
from app.graph.schemas import RiskGraphState


def prepare_context(
    state: RiskGraphState,
) -> RiskGraphState:
    assessment = state["risk_assessment"]

    factors = "\n".join(
        (
            f"- {factor.name}: "
            f"{factor.description} "
            f"(score: {factor.score})"
        )
        for service_assessment in (
            assessment.service_assessments
        )
        for factor in service_assessment.factors
    )

    changed_files = (
        "\n".join(
            f"- {file.filename} "
            f"({file.status}, "
            f"+{file.additions}/-{file.deletions})"
            for file in getattr(
                assessment,
                "changed_files",
                [],
            )
        )
        or "Changed file details unavailable."
    )

    context = f"""
Repository: {assessment.repository}

Change Request:
- Number: {assessment.change_request_number}
- Title: {assessment.change_request_title}

Affected services:
{chr(10).join(
    f"- {service}"
    for service in assessment.affected_services
) or "- None identified"}

Change types:
{chr(10).join(
    f"- {change_type}"
    for change_type in assessment.change_types
) or "- None identified"}

Risk signals:
{chr(10).join(
    f"- {signal}"
    for signal in assessment.risk_signals
) or "- None identified"}

Files changed: {assessment.files_changed}
Lines added: {assessment.lines_added}
Lines deleted: {assessment.lines_deleted}

Deterministic risk score:
{assessment.overall_score}/100

Deterministic risk level:
{assessment.overall_level.value}

Risk factors:
{factors or "- No historical risk factors."}

Changed files:
{changed_files}
""".strip()

    return {
        **state,
        "context": context,
    }


def generate_analysis(
    state: RiskGraphState,
) -> RiskGraphState:
    settings = get_settings()

    # llm = ChatOpenAI(
    #     model=settings.openai_model,
    #     api_key=settings.openai_api_key,
    #     temperature=0,
    # )
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=0,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are a senior site reliability engineer reviewing
a proposed production deployment.

The deployment risk score has already been calculated by
a deterministic risk engine.

You MUST NOT change, reinterpret, or recalculate the
risk score.

Your job is to explain the evidence and provide practical
deployment guidance.

Focus on:
1. What changed.
2. Why the historical evidence matters.
3. What makes this deployment risky or safe.
4. What should be done before and during deployment.

Do not invent incidents, metrics, services, or facts that
are not present in the provided context.

Return exactly two sections:

EXPLANATION:
A concise explanation in 2-4 paragraphs.

RECOMMENDATION:
A concise actionable deployment recommendation.
""",
            ),
            (
                "human",
                "{context}",
            ),
        ]
    )

    chain = prompt | llm

    response = chain.invoke(
        {
            "context": state["context"],
        }
    )

    content = response.content

    explanation = content
    recommendation = ""

    if "RECOMMENDATION:" in content:
        explanation, recommendation = (
            content.split(
                "RECOMMENDATION:",
                1,
            )
        )

    explanation = explanation.replace(
        "EXPLANATION:",
        "",
        1,
    ).strip()

    recommendation = recommendation.strip()

    return {
        **state,
        "explanation": explanation,
        "recommendation": recommendation,
    }