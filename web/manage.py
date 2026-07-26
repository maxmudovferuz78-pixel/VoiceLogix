#!/usr/bin/env python
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# .env faylini loyiha tub papkasidan (web/ dan bir daraja yuqoridan) o'qiydi
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django o'rnatilmagan. 'pip install -r ../requirements.txt' bajaring."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
