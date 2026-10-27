
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
    filename="agent_control.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
    agent_name = os.getenv(
        "FOUNDRY_AGENT_NAME",
        "infrastructure-helpdesk",
    )

    if not endpoint:
        print("ERROR: FOUNDRY_PROJECT_ENDPOINT is missing in .env")
        return

    print("\n--- Foundry Agent Control ---")
    print(f"Agent: {agent_name}")
    print("1. Disable agent")
    print("2. Enable agent")

    choice = input("Choose an operation (1/2): ").strip()

    if choice not in ("1", "2"):
        print("Invalid choice. Enter 1 or 2.")
        return

    operation = "disable" if choice == "1" else "enable"

    credential = None
    project = None

    try:
        credential = DefaultAzureCredential()

        project = AIProjectClient(
            endpoint=endpoint,
            credential=credential,
        )

        print(f"\nRequesting agent {operation}...")

        if operation == "disable":
            project.agents.disable(agent_name=agent_name)
        else:
            project.agents.enable(agent_name=agent_name)

        logger.info(
            "Agent operation succeeded | agent=%s | operation=%s",
            agent_name,
            operation,
        )

        print(f"SUCCESS: Agent {operation} operation accepted.")

        # Verify that the agent definition can still be retrieved.
        agent = project.agents.get(agent_name=agent_name)

        print("Agent definition still exists.")
        print("Agent name:", getattr(agent, "name", agent_name))
        print("Operation log: agent_control.log")

        logger.info(
            "Agent definition verified | agent=%s",
            agent_name,
        )

    except ClientAuthenticationError:
        logger.exception("Azure authentication failed")
        print("Authentication failed. Check your Azure login.")

    except HttpResponseError as exc:
        logger.error(
            "Foundry management API error | status=%s | message=%s",
            exc.status_code,
            exc.message,
        )
        print(f"Foundry API error: HTTP {exc.status_code}")
        print(exc.message)
        print("Check agent type and management permissions.")

    except Exception as exc:
        import traceback

        print(f"Error type: {type(exc).__name__}")
        print(f"Error details: {exc}")
        traceback.print_exc()

    except Exception:
        logger.exception("Unexpected agent management failure")
        print("Unexpected error. Check agent_control.log.")

    finally:
        if project is not None:
            project.close()

        if credential is not None:
            credential.close()


if __name__ == "__main__":
    main()
