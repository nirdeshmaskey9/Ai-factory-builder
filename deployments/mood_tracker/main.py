import os
from uvicorn import run


def main() -> None:
    port = int(os.environ.get("PORT", "8038"))
    run("app:app", host="127.0.0.1", port=port, reload=False, log_level="warning")


if __name__ == "__main__":
    main()

