from __future__ import annotations

import structlog

from app.config.settings import settings

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Synthetic demo data – used while Graph API integration is a placeholder
# ---------------------------------------------------------------------------

_SAMPLE_SHAREPOINT_DOCS = [
    {
        "id": "sp-doc-001",
        "source_url": "https://contoso.sharepoint.com/sites/hr/Documents/Onboarding_Guide_2024.pdf",
        "source_type": "sharepoint",
        "title": "New Hire Onboarding Guide 2024",
        "text": (
            "Welcome to Contoso! This guide covers your first 90 days. "
            "Week 1: IT setup, badge access, and team introductions. "
            "Week 2: Product training and shadow sessions with senior engineers. "
            "Week 4: First project assignment. Benefits enrollment deadline is Day 30. "
            "Your HR contact is hr-support@contoso.com for any questions."
        ),
    },
    {
        "id": "sp-doc-002",
        "source_url": "https://contoso.sharepoint.com/sites/eng/Documents/Engineering_Standards.docx",
        "source_type": "sharepoint",
        "title": "Engineering Standards & Practices",
        "text": (
            "All code must pass CI before merging. Branch naming convention: "
            "feature/<ticket-id>-short-description. PRs require two approvals. "
            "Deploy to staging every Wednesday; production every other Friday. "
            "On-call rotation is managed via PagerDuty. Runbooks live in Confluence."
        ),
    },
]

_SAMPLE_TEAMS_TRANSCRIPTS = [
    {
        "id": "teams-001",
        "source_url": "https://teams.microsoft.com/l/meeting/transcript/abc123",
        "source_type": "teams",
        "title": "Q1 All-Hands Meeting – Engineering",
        "text": (
            "VP Engineering: Our Q1 priorities are reliability, reducing P0 incidents by 40%, "
            "and launching the self-serve billing portal. "
            "EM: The new hire cohort starts February 1st. Please add them to Slack channels. "
            "DevOps: Migration to Kubernetes is 70% complete; target GA is end of Q2."
        ),
    },
]


class GraphAPIClient:
    """Client for the Microsoft Graph API (M365 data ingestion)."""

    def __init__(self) -> None:
        self.tenant_id: str = settings.AZURE_TENANT_ID
        self.client_id: str = settings.AZURE_CLIENT_ID
        self.client_secret: str = settings.AZURE_CLIENT_SECRET
        self._token: str | None = None

    async def get_access_token(self) -> str:
        """
        Obtain an OAuth2 access token via the client credentials flow.

        # TODO: implement OAuth2 client credentials flow using httpx
        #   POST https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token
        #   Body: grant_type=client_credentials
        #         &client_id={client_id}
        #         &client_secret={client_secret}
        #         &scope=https://graph.microsoft.com/.default
        #   Cache the token and refresh before expiry (typically 3600 s).
        """
        logger.warning(
            "graph_client.get_access_token.placeholder",
            message="OAuth2 flow not implemented – returning empty token.",
        )
        return ""

    async def list_sharepoint_documents(self, site_id: str) -> list[dict]:
        """
        Return documents from a SharePoint site drive.

        # TODO: call GET /sites/{site_id}/drive/root/children via Graph API
        #   Headers: Authorization: Bearer {token}
        #   Paginate using @odata.nextLink.
        #   For each file item, download content with /content endpoint and
        #   extract text (PDF → pypdf, DOCX → python-docx, etc.).
        """
        logger.warning(
            "graph_client.list_sharepoint_documents.placeholder",
            site_id=site_id,
            message="Returning synthetic demo documents.",
        )
        return _SAMPLE_SHAREPOINT_DOCS

    async def get_teams_transcripts(self, team_id: str) -> list[dict]:
        """
        Return meeting transcripts for a Teams team.

        # TODO: call GET /teams/{team_id}/channels/{channelId}/messages
        #   and follow /replies to collect full threads.
        #   For meeting recordings, use GET /communications/callRecords
        #   and fetch the associated VTT transcript file.
        """
        logger.warning(
            "graph_client.get_teams_transcripts.placeholder",
            team_id=team_id,
            message="Returning synthetic demo transcripts.",
        )
        return _SAMPLE_TEAMS_TRANSCRIPTS


graph_client = GraphAPIClient()
