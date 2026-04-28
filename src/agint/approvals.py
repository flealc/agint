from typing import Any

def request_approval(action: str, args: dict[str, Any]) -> bool:
  print(f"\nApproval required: {action}")

  if args:
    print("Arguments:")
    for key, value in args.items():
      print(f"  {key}: {value}")

  answer = input("Approve? y/N: ").strip().lower()
  return answer == "y"