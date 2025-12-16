#!/usr/bin/env python3
import sys
import logging
import argparse
from pathlib import Path

from app.agent.orchestrator import Orchestrator
from app.explain.formatter import BuildFormatter

def setup_logging(verbose=False):
    """Configure logging based on verbosity"""
    if verbose:
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s - %(message)s'
        )
    else:
        # Only show warnings and errors in non-verbose mode
        logging.basicConfig(
            level=logging.WARNING,
            format='%(levelname)s - %(message)s'
        )

def print_banner():
    """Print welcome banner"""
    print("\n" + "="*70)
    print("                        PC BUILDER AGENT")
    print("="*70)
    print("\nDescribe what you need and I'll design your perfect PC build.")
    print("\nEXAMPLES:")
    print("  - I need a gaming PC for $1500 that can handle 1440p")
    print("  - Build me a quiet workstation for video editing under $2000")
    print("  - I want a compact PC for machine learning with RTX 4090")
    print("\nCOMMANDS:")
    print("  - Type your requirements and press Enter")
    print("  - Type 'quit' or 'exit' to stop")
    print("  - Press Ctrl+C to interrupt")
    print("="*70 + "\n")

def print_thinking():
    """Show a friendly thinking message"""
    print("\nGenerating your PC build... (this may take 30-60 seconds)\n")

def main():
    parser = argparse.ArgumentParser(
        description="AI-powered PC build recommendation system",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed logs during build generation'
    )
    parser.add_argument(
        '--quick',
        metavar='REQUIREMENTS',
        type=str,
        help='Generate a single build and exit (e.g., --quick "gaming PC for $1500")'
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    orchestrator = Orchestrator()
    formatter = BuildFormatter()

    # Quick mode: single build then exit
    if args.quick:
        try:
            print_thinking()
            constraints = orchestrator.interpreter.extract_constraints(args.quick)
            build = orchestrator._plan_validate_loop(constraints)
            output = formatter.format_build(build, constraints)
            print("\n" + output + "\n")
            return 0
        except Exception as e:
            print(f"\nERROR: {e}\n")
            if args.verbose:
                logging.error(f"Failed to generate build: {e}", exc_info=True)
            return 1

    # Interactive mode
    print_banner()

    while True:
        try:
            user_input = input("Your requirements: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nThanks for using PC Builder Agent. Goodbye!\n")
                break

            if len(user_input) < 10:
                print("Please provide more details (at least 10 characters).\n")
                continue

            print_thinking()

            # Extract constraints
            constraints = orchestrator.interpreter.extract_constraints(user_input)

            # Generate and validate build
            build = orchestrator._plan_validate_loop(constraints)

            # Format output
            output = formatter.format_build(build, constraints)

            print("\n" + output)
            print("\n" + "-"*70)
            print("Build complete! Want another? Just describe your requirements.")
            print("-"*70 + "\n")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!\n")
            break
        except Exception as e:
            print(f"\nERROR: {e}")
            print("Try rephrasing your requirements or being more specific.\n")
            if args.verbose:
                logging.error(f"Failed to generate build: {e}", exc_info=True)

    return 0

if __name__ == "__main__":
    sys.exit(main())
