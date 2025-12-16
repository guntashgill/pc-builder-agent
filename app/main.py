#!/usr/bin/env python3
import sys
import logging
from pathlib import Path

from app.agent.orchestrator import Orchestrator
from app.explain.formatter import BuildFormatter

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

def main():
    print("\n" + "="*70)
    print("PC BUILDER AGENT")
    print("="*70)
    print("\nDescribe your ideal PC build and I'll design one for you.")
    print("Example: 'I need a gaming PC for $1500 that can handle 1440p'")
    print("\nType 'quit' or 'exit' to stop.\n")

    orchestrator = Orchestrator()
    formatter = BuildFormatter()

    while True:
        try:
            user_input = input("Your requirements: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            if len(user_input) < 10:
                print("Please provide more details (at least 10 characters).\n")
                continue

            print("\nGenerating your PC build...\n")

            # Extract constraints
            constraints = orchestrator.interpreter.extract_constraints(user_input)

            # Generate and validate build
            build = orchestrator._plan_validate_loop(constraints)

            # Format output
            output = formatter.format_build(build, constraints)

            print("\n" + output + "\n")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")
            logging.error(f"Failed to generate build: {e}", exc_info=True)

if __name__ == "__main__":
    main()
