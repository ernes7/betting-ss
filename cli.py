"""NFL Stats CLI

Interactive menu-based interface for extracting NFL stats and making predictions.
"""

from cli_utils.extract import extract_rankings
from cli_utils.predict import predict_game


def display_menu():
    """Display the main menu."""
    print("\n" + "=" * 70)
    print("NFL STATS & BETTING ANALYSIS")
    print("=" * 70)
    print("\n1. Extract Rankings")
    print("2. Predict Game")
    print("3. Exit")
    print("\n" + "=" * 70)


def main():
    """Main CLI entry point with interactive menu."""
    while True:
        display_menu()
        choice = input("\nSelect option (1-3): ").strip()

        if choice == "1":
            print("\n")
            extract_rankings()
            input("\nPress Enter to continue...")

        elif choice == "2":
            predict_game()
            input("\nPress Enter to continue...")

        elif choice == "3":
            print("\nExiting... Goodbye!")
            break

        else:
            print("\n⚠️  Invalid option. Please select 1, 2, or 3.")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
