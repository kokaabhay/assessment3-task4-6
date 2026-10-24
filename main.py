
import os
import logging

from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ServiceRequestError,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def main(query:str):
    endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
    agent_name = os.getenv("FOUNDRY_AGENT_NAME")
    agent_version = os.getenv("FOUNDRY_AGENT_VERSION", "1")

    if not endpoint or not agent_name:
        raise ValueError(
            "Missing FOUNDRY_PROJECT_ENDPOINT or "
            "FOUNDRY_AGENT_NAME in .env"
        )

    credential = None
    project = None

    try:
        logger.info("Connecting to Microsoft Foundry")

        credential = DefaultAzureCredential()

        project = AIProjectClient(
            endpoint=endpoint,
            credential=credential,
        )

        # Invoke the specified, existing agent version.
        openai = project.get_openai_client()

        logger.info(
            "Invoking agent=%s version=%s",
            agent_name,
            agent_version,
        )

        response = openai.responses.create(
            input=(
                query.strip()
            ),
            extra_body={
                "agent_reference": {
                    "name": agent_name,
                    "type": "agent_reference",
                    "version": agent_version,
                }
            },
        )

        print("\n--- Agent Response ---")
        print(response.output_text)

        print("\n--- Request Details ---")
        print("Response ID:", getattr(response, "id", "Not returned"))
        print("Agent name:", agent_name)
        print("Agent version:", agent_version)

        logger.info("Agent invocation completed successfully")

    except ClientAuthenticationError:
        logger.exception(
            "Authentication failed. Check az login, tenant, "
            "and credential configuration."
        )

    except HttpResponseError as exc:
        logger.error(
            "Foundry API error | status=%s | message=%s",
            exc.status_code,
            exc.message,
        )
        logger.error(
            "Check project endpoint, agent name/version, "
            "deployment status, and RBAC permissions."
        )

    except ServiceRequestError:
        logger.exception(
            "Network or connection failure while contacting Foundry"
        )

    except (ValueError, KeyError) as exc:
        logger.error("Configuration error: %s", exc)

    except Exception:
        logger.exception("Unexpected failure during agent invocation")

    finally:
        if project is not None:
            project.close()

        if credential is not None:
            credential.close()


if __name__ == "__main__":
    query=input("Ask your query:")
    main(query)
